"""
Value board computation service.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from math import exp

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

    def _team_recent_stats(self, team_name: str) -> TeamRecentStats:
        team_abbr = self._team_abbrev_from_name(team_name) if team_name else None
        if not team_abbr:
            return TeamRecentStats(net_rating=0.0, pace=100.0)
        rows = self.db.table("team_game_stats").select(
            "offensive_rating,defensive_rating,pace"
        ).eq("team_abbreviation", team_abbr).order("game_date", desc=True).limit(10).execute()
        data = rows.data or []
        if not data:
            return TeamRecentStats(net_rating=0.0, pace=100.0)
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
        return TeamRecentStats(net_rating=net, pace=pace_avg)

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

    def _build_game_model(self, game: Dict[str, Any]) -> Dict[str, float]:
        home_name = game.get("home_team")
        away_name = game.get("away_team")
        home_stats = self._team_recent_stats(home_name)
        away_stats = self._team_recent_stats(away_name)
        home_court = 1.5
        margin = (home_stats.net_rating - away_stats.net_rating) / 2.0 + home_court
        total = self._predicted_total(home_stats, away_stats)
        return {
            "home_margin": margin,
            "total": total,
        }

    def get_value_board(self, window_days: int = 2) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        end = now + timedelta(days=window_days)
        games = self.db.table("games").select("id,home_team,away_team,commence_time").gte(
            "commence_time", now.isoformat()
        ).lte("commence_time", end.isoformat()).order("commence_time").execute()

        results: List[Dict[str, Any]] = []
        for game in games.data or []:
            model = self._build_game_model(game)
            consensus = self.odds_service.consensus_for_game(game, None)

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
                })

        return results


_value_service: Optional[ValueService] = None


def get_value_service() -> ValueService:
    global _value_service
    if _value_service is None:
        _value_service = ValueService()
    return _value_service
