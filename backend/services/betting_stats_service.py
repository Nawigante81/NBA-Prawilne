"""
Betting stats service for ATS and O/U.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
import statistics

from db import get_db
from services.odds_service import get_odds_service


class BettingStatsService:
    def __init__(self, db=None, odds_service=None):
        self.db = db
        self.odds_service = odds_service
        if self.db is None:
            try:
                self.db = get_db()
            except ValueError:
                self.db = None
        if self.odds_service is None and self.db is not None:
            self.odds_service = get_odds_service()

    def _find_game_for_result(self, home_team: str, away_team: str, game_date_value: str | date | None) -> Optional[Dict[str, Any]]:
        if not self.db:
            raise RuntimeError("Supabase client not configured")
        if not game_date_value:
            return None
        if isinstance(game_date_value, date):
            d = game_date_value
        else:
            try:
                d = datetime.fromisoformat(str(game_date_value)).date()
            except Exception:
                return None
        start = datetime(d.year, d.month, d.day)
        end = start + timedelta(days=1)
        resp = self.db.table("games").select("id,commence_time,home_team,away_team").eq("home_team", home_team).eq(
            "away_team", away_team
        ).gte("commence_time", start.isoformat()).lt("commence_time", end.isoformat()).execute()
        rows = resp.data or []
        return rows[0] if rows else None

    def _closing_line(self, game: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.odds_service:
            raise RuntimeError("Odds service not configured")
        commence = game.get("commence_time")
        if not commence:
            return None
        cutoff = datetime.fromisoformat(str(commence).replace("Z", "+00:00"))
        consensus = self.odds_service.consensus_for_game(game, cutoff)
        self.odds_service.upsert_closing_lines(game, consensus)
        return consensus

    def _ats_result(self, team_score: float, opp_score: float, spread: float) -> str:
        adjusted = team_score + spread
        if adjusted > opp_score:
            return "W"
        if adjusted < opp_score:
            return "L"
        return "P"

    def compute_team_betting_stats(self, team_abbrev: str, window: int = 20) -> Dict[str, Any]:
        if not self.db:
            raise RuntimeError("Supabase client not configured")
        team_resp = self.db.table("teams").select("full_name,abbreviation").eq("abbreviation", team_abbrev.upper()).execute()
        if not team_resp.data:
            return {"team": team_abbrev.upper(), "has_data": False}
        team = team_resp.data[0]
        team_name = team.get("full_name")

        results_resp = self.db.table("game_results").select("*").or_(
            f"home_team.eq.{team_name},away_team.eq.{team_name}"
        ).order("game_date", desc=True).limit(max(82, window)).execute()
        results = results_resp.data or []

        def _calc(rows: List[Dict[str, Any]]):
            ats_w = ats_l = ats_p = 0
            ou_o = ou_u = ou_p = 0
            spread_diffs = []
            total_diffs = []
            totals = []

            for r in rows:
                home_team = r.get("home_team")
                away_team = r.get("away_team")
                home_score = r.get("home_score")
                away_score = r.get("away_score")
                if home_score is None or away_score is None:
                    continue

                game = self._find_game_for_result(home_team, away_team, r.get("game_date"))
                if not game:
                    continue

                consensus = self._closing_line(game)
                if not consensus:
                    continue

                team_is_home = team_name == home_team
                team_score = float(home_score)
                opp_score = float(away_score)
                if not team_is_home:
                    team_score, opp_score = opp_score, team_score

                spreads = consensus.get("spreads") or {}
                spread_line = spreads.get("home" if team_is_home else "away")
                if spread_line and spread_line.get("point") is not None:
                    spread = float(spread_line.get("point"))
                    result = self._ats_result(team_score, opp_score, spread)
                    if result == "W":
                        ats_w += 1
                    elif result == "L":
                        ats_l += 1
                    else:
                        ats_p += 1
                    spread_diffs.append(team_score + spread - opp_score)

                totals_info = consensus.get("totals") or {}
                total_line = totals_info.get("point")
                if total_line is not None:
                    total_score = float(home_score) + float(away_score)
                    totals.append(total_score)
                    if total_score > float(total_line):
                        ou_o += 1
                    elif total_score < float(total_line):
                        ou_u += 1
                    else:
                        ou_p += 1
                    total_diffs.append(total_score - float(total_line))

            ats_den = ats_w + ats_l
            ou_den = ou_o + ou_u
            return {
                "ats": {
                    "w": ats_w,
                    "l": ats_l,
                    "p": ats_p,
                    "avg_spread_diff": float(statistics.mean(spread_diffs)) if spread_diffs else None,
                    "win_pct": (ats_w / ats_den) if ats_den > 0 else None,
                },
                "ou": {
                    "o": ou_o,
                    "u": ou_u,
                    "p": ou_p,
                    "avg_total_diff": float(statistics.mean(total_diffs)) if total_diffs else None,
                    "over_pct": (ou_o / ou_den) if ou_den > 0 else None,
                },
                "avg_total_points": float(statistics.mean(totals)) if totals else None,
                "games_count": len(rows),
            }

        last_window = results[:window]
        season = results[:82]
        return {
            "team": team.get("abbreviation"),
            "team_name": team_name,
            "window": window,
            "last_window": _calc(last_window) if last_window else None,
            "season": _calc(season) if season else None,
            "has_data": bool(results),
            "computed_at": datetime.utcnow().isoformat(),
        }


_betting_stats_service: Optional[BettingStatsService] = None


def get_betting_stats_service() -> BettingStatsService:
    global _betting_stats_service
    if _betting_stats_service is None:
        _betting_stats_service = BettingStatsService()
    return _betting_stats_service
