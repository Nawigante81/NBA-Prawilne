"""
Value board computation service.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Iterable
from math import exp
from time import monotonic
from collections import defaultdict

from db import get_db
from settings import settings
from services.betting_math import expected_value, implied_probability, kelly_criterion
from services.odds_service import get_odds_service
from services.quality_gates import get_quality_gate_service


@dataclass
class TeamRecentStats:
    net_rating: float
    pace: float


class ValueService:
    """Compute value board and picks."""

    def __init__(self):
        self.db = get_db()
        self.odds_service = get_odds_service()
        self.quality_gates = get_quality_gate_service()
        self._team_name_map: Dict[str, str] = {}
        self._value_board_cache: Dict[str, Any] = {}
        self._value_board_cache_ts: Optional[datetime] = None

    def _team_abbrev_from_name(self, name: str) -> Optional[str]:
        if not name:
            return None
        if name in self._team_name_map:
            return self._team_name_map[name]
        result = self.db.table("teams").select("abbreviation,full_name").eq("full_name", name).limit(1).execute()
        if result.data:
            abbr = result.data[0].get("abbreviation")
            if abbr:
                self._team_name_map[name] = abbr
                return abbr
        return None

    def _refresh_team_map(self) -> None:
        if self._team_name_map:
            return
        result = self.db.table("teams").select("abbreviation,full_name").execute()
        for row in result.data or []:
            name = row.get("full_name")
            abbr = row.get("abbreviation")
            if name and abbr:
                self._team_name_map[name] = abbr

    def _build_team_stats_map(self, team_abbrs: Iterable[str]) -> Dict[str, TeamRecentStats]:
        abbrs = [abbr for abbr in set(team_abbrs) if abbr]
        if not abbrs:
            return {}
        limit_rows = min(len(abbrs) * 12, 360)
        rows = self.db.table("team_game_stats").select(
            "team_abbreviation,offensive_rating,defensive_rating,pace,game_date"
        ).in_("team_abbreviation", abbrs).order("game_date", desc=True).limit(limit_rows).execute()
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in rows.data or []:
            abbr = row.get("team_abbreviation")
            if not abbr:
                continue
            if len(grouped[abbr]) < 10:
                grouped[abbr].append(row)
        stats_map: Dict[str, TeamRecentStats] = {}
        for abbr, data in grouped.items():
            net_ratings = []
            paces = []
            for r in data:
                off = r.get("offensive_rating")
                deff = r.get("defensive_rating")
                pace = r.get("pace")
                if off is not None and deff is not None:
                    net_ratings.append(float(off) - float(deff))
                if pace is not None:
                    paces.append(float(pace))
            net = sum(net_ratings) / len(net_ratings) if net_ratings else 0.0
            pace_avg = sum(paces) / len(paces) if paces else 100.0
            stats_map[abbr] = TeamRecentStats(net_rating=net, pace=pace_avg)
        return stats_map

    def _team_recent_stats(self, team_name: str, stats_map: Dict[str, TeamRecentStats]) -> TeamRecentStats:
        team_abbr = self._team_abbrev_from_name(team_name) if team_name else None
        if not team_abbr:
            return TeamRecentStats(net_rating=0.0, pace=100.0)
        if team_abbr in stats_map:
            return stats_map[team_abbr]
        return TeamRecentStats(net_rating=0.0, pace=100.0)

    def _win_prob_from_margin(self, margin: float) -> float:
        return 1.0 / (1.0 + exp(-margin / 8.0))

    def _cover_prob(self, margin: float, spread: float) -> float:
        return 1.0 / (1.0 + exp(-(margin - spread) / 8.0))

    def _total_over_prob(self, predicted_total: float, line: float) -> float:
        return 1.0 / (1.0 + exp((line - predicted_total) / 8.0))

    def _predicted_total(self, home: TeamRecentStats, away: TeamRecentStats) -> float:
        pace = (home.pace + away.pace) / 2.0
        off_sum = (home.net_rating + away.net_rating) / 2.0
        return 220.0 + (pace - 100.0) * 0.7 + off_sum * 0.6

    def _build_game_model(self, game: Dict[str, Any], stats_map: Dict[str, TeamRecentStats]) -> Dict[str, float]:
        home_name = game.get("home_team")
        away_name = game.get("away_team")
        home_stats = self._team_recent_stats(home_name, stats_map)
        away_stats = self._team_recent_stats(away_name, stats_map)
        home_court = 1.5
        margin = (home_stats.net_rating - away_stats.net_rating) / 2.0 + home_court
        total = self._predicted_total(home_stats, away_stats)
        return {
            "home_margin": margin,
            "total": total,
            "home_pace": home_stats.pace,
            "away_pace": away_stats.pace,
        }

    def _why_bullets(
        self,
        market_type: str,
        selection: str,
        line: Optional[float],
        price: Optional[float],
        model: Dict[str, float],
        model_prob: float,
        edge: float,
        ev_val: float,
        margin_override: Optional[float] = None,
    ) -> List[str]:
        bullets: List[str] = []
        if market_type == "spreads":
            margin = margin_override if margin_override is not None else model.get("home_margin", 0.0)
            bullets.append(f"Model margin: {margin:+.1f} (HCA +1.5)")
            if line is not None:
                bullets.append(f"Konsensus linia: {line:+.1f}")
            if price is not None:
                bullets.append(f"Kurs: {price}")
        elif market_type == "totals":
            pace = (model.get("home_pace", 100.0) + model.get("away_pace", 100.0)) / 2.0
            bullets.append(f"Pred total: {model.get('total', 0.0):.1f} (pace {pace:.1f})")
            if line is not None:
                bullets.append(f"Konsensus linia: {line:.1f}")
            if price is not None:
                bullets.append(f"Kurs: {price}")
        else:
            bullets.append(f"Model win prob: {(model_prob * 100):.1f}%")
            if price is not None:
                bullets.append(f"Kurs: {price}")
        bullets.append(f"Edge: {(edge * 100):+.1f} pp")
        bullets.append(f"EV: {(ev_val * 100):+.1f}%")
        return bullets[:4]

    def _timeout_rows(self, games: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for game in games:
            commence_time = game.get("commence_time")
            home = game.get("home_team")
            rows.append({
                "game_id": game.get("id"),
                "market_type": "h2h",
                "selection": home or "Home",
                "point": None,
                "price": None,
                "implied_prob": None,
                "model_prob": 0.5,
                "edge_prob": 0.0,
                "ev": 0.0,
                "kelly_fraction": 0.0,
                "commence_time": commence_time,
                "decision": "NO_BET",
                "reasons": ["TIMEOUT"],
                "why_bullets": [],
                "skip_gates": True,
            })
        return rows

    def get_value_board(self, window_days: int = 2) -> List[Dict[str, Any]]:
        cache_key = f"{window_days}:{settings.value_board_max_games}"
        now = datetime.utcnow()
        if self._value_board_cache_ts:
            cache_age = (now - self._value_board_cache_ts).total_seconds()
            if cache_age < settings.value_board_cache_seconds:
                cached = self._value_board_cache.get(cache_key)
                if cached is not None:
                    return [dict(row) for row in cached]

        start_ts = monotonic()
        end = now + timedelta(days=window_days)
        games = self.db.table("games").select("id,home_team,away_team,commence_time").gte(
            "commence_time", now.isoformat()
        ).lte("commence_time", end.isoformat()).order("commence_time").limit(
            settings.value_board_max_games
        ).execute()

        results: List[Dict[str, Any]] = []
        games_list = games.data or []
        if not games_list:
            self._value_board_cache[cache_key] = []
            self._value_board_cache_ts = now
            return []

        self._refresh_team_map()
        team_abbrs = []
        for game in games_list:
            home_name = game.get("home_team")
            away_name = game.get("away_team")
            if home_name:
                team_abbrs.append(self._team_name_map.get(home_name, ""))
            if away_name:
                team_abbrs.append(self._team_name_map.get(away_name, ""))

        stats_map = self._build_team_stats_map(team_abbrs)

        allowlist = [b.strip() for b in settings.odds_bookmakers_allowlist if b.strip()][:3]
        market_types = ["spreads", "spread", "totals", "total", "h2h"]
        game_ids = [g.get("id") for g in games_list if g.get("id")]
        snapshots = []
        if game_ids:
            query = self.db.table("odds_snapshots").select(
                "game_id,bookmaker_key,market_type,outcome_name,team,point,price,ts"
            ).in_("game_id", game_ids).in_("market_type", market_types)
            if allowlist:
                query = query.in_("bookmaker_key", allowlist)
            snapshots = query.execute().data or []
        snapshots_by_game: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in snapshots:
            game_id = row.get("game_id")
            if game_id:
                snapshots_by_game[game_id].append(row)

        for idx, game in enumerate(games_list):
            if monotonic() - start_ts > settings.value_board_timeout_seconds:
                results.extend(self._timeout_rows(games_list[idx:]))
                break
            model = self._build_game_model(game, stats_map)
            consensus = self.odds_service.consensus_for_game_from_rows(
                game,
                None,
                snapshots_by_game.get(game.get("id"), []),
            )

            # Spread
            for side_key, label in [("home", game.get("home_team")), ("away", game.get("away_team"))]:
                spread_line = (consensus.get("spreads") or {}).get(side_key)
                if not spread_line:
                    continue
                line = spread_line.get("point")
                price = spread_line.get("price")
                if line is None or price is None:
                    continue
                margin = model.get("home_margin")
                if side_key == "away":
                    margin = -margin
                model_prob = self._cover_prob(margin, float(line))
                implied = implied_probability(float(price), "american")
                ev_val = expected_value(model_prob, float(price), "american", 1.0)
                edge = model_prob - implied
                stake = kelly_criterion(model_prob, float(price), "american", fraction=0.5, max_stake_pct=settings.max_stake_pct)

                results.append({
                    "game_id": game.get("id"),
                    "market_type": "spreads",
                    "selection": label,
                    "point": line,
                    "price": price,
                    "implied_prob": implied,
                    "model_prob": model_prob,
                    "edge_prob": edge,
                    "ev": ev_val,
                    "kelly_fraction": stake,
                    "commence_time": game.get("commence_time"),
                    "why_bullets": self._why_bullets(
                        "spreads", label, line, price, model, model_prob, edge, ev_val, margin
                    ),
                })

            # Totals
            totals = consensus.get("totals") or {}
            total_point = totals.get("point")
            for outcome_key, is_over in [("over", True), ("under", False)]:
                side = totals.get(outcome_key) or {}
                price = side.get("price")
                if total_point is None or price is None:
                    continue
                predicted_total = model.get("total")
                model_prob = self._total_over_prob(predicted_total, float(total_point))
                if not is_over:
                    model_prob = 1.0 - model_prob
                implied = implied_probability(float(price), "american")
                ev_val = expected_value(model_prob, float(price), "american", 1.0)
                edge = model_prob - implied
                stake = kelly_criterion(model_prob, float(price), "american", fraction=0.5, max_stake_pct=settings.max_stake_pct)

                results.append({
                    "game_id": game.get("id"),
                    "market_type": "totals",
                    "selection": side.get("team") or outcome_key.capitalize(),
                    "point": total_point,
                    "price": price,
                    "implied_prob": implied,
                    "model_prob": model_prob,
                    "edge_prob": edge,
                    "ev": ev_val,
                    "kelly_fraction": stake,
                    "commence_time": game.get("commence_time"),
                    "why_bullets": self._why_bullets(
                        "totals", side.get("team") or outcome_key.capitalize(), total_point, price, model, model_prob, edge, ev_val
                    ),
                })

            # H2H
            for side_key, label in [("home", game.get("home_team")), ("away", game.get("away_team"))]:
                h2h_line = (consensus.get("h2h") or {}).get(side_key)
                if not h2h_line:
                    continue
                price = h2h_line.get("price")
                if price is None:
                    continue
                margin = model.get("home_margin")
                model_prob = self._win_prob_from_margin(margin)
                if side_key == "away":
                    model_prob = 1.0 - model_prob
                implied = implied_probability(float(price), "american")
                ev_val = expected_value(model_prob, float(price), "american", 1.0)
                edge = model_prob - implied
                stake = kelly_criterion(model_prob, float(price), "american", fraction=0.5, max_stake_pct=settings.max_stake_pct)

                results.append({
                    "game_id": game.get("id"),
                    "market_type": "h2h",
                    "selection": label,
                    "point": None,
                    "price": price,
                    "implied_prob": implied,
                    "model_prob": model_prob,
                    "edge_prob": edge,
                    "ev": ev_val,
                    "kelly_fraction": stake,
                    "commence_time": game.get("commence_time"),
                    "why_bullets": self._why_bullets(
                        "h2h", label, None, price, model, model_prob, edge, ev_val
                    ),
                })

        self._value_board_cache[cache_key] = [dict(row) for row in results]
        self._value_board_cache_ts = datetime.utcnow()
        return results


_value_service: Optional[ValueService] = None


def get_value_service() -> ValueService:
    global _value_service
    if _value_service is None:
        _value_service = ValueService()
    return _value_service
