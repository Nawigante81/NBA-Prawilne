"""
AI recommendation service for betting decisions.
Builds lightweight model-based suggestions on top of existing value board logic.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from db import get_db
from services.value_service import get_value_service
from services.quality_gates import get_quality_gate_service


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _confidence(edge: Optional[float], model_prob: Optional[float]) -> float:
    edge_val = edge or 0.0
    prob_val = model_prob or 0.5
    base = 0.5 + _clamp(edge_val, -0.12, 0.12) * 2.8
    spread = abs(prob_val - 0.5) * 0.65
    return _clamp(base + spread, 0.05, 0.95)


class AIRecommendationService:
    """Generate AI recommendations for a team's next game."""

    def __init__(self) -> None:
        self.db = get_db()
        self.value_service = get_value_service()
        self.quality_gates = get_quality_gate_service()

    def _team_row(self, team_abbrev: str) -> Optional[Dict[str, Any]]:
        resp = self.db.table("teams").select("full_name,abbreviation").eq(
            "abbreviation", team_abbrev.upper()
        ).limit(1).execute()
        return (resp.data or [None])[0]

    def _next_game(self, team_name: str) -> Optional[Dict[str, Any]]:
        now_iso = datetime.utcnow().isoformat()
        resp = self.db.table("games").select(
            "id,commence_time,home_team,away_team"
        ).or_(f"home_team.eq.{team_name},away_team.eq.{team_name}").gte(
            "commence_time", now_iso
        ).order("commence_time").limit(1).execute()
        return (resp.data or [None])[0]

    def _risk_flags(self, game_id: str) -> List[str]:
        flags: List[str] = []
        latest_ts_resp = self.db.table("odds_snapshots").select("ts").eq(
            "game_id", game_id
        ).order("ts", desc=True).limit(1).execute()
        latest_ts = _parse_iso_datetime((latest_ts_resp.data or [{}])[0].get("ts"))
        if latest_ts:
            snapshot_age_hours = (datetime.utcnow() - latest_ts.replace(tzinfo=None)).total_seconds() / 3600
            stale_hours = float(os.getenv("ODDS_STALE_HOURS", "12"))
            if snapshot_age_hours > stale_hours:
                flags.append("LINE_STALE")
        try:
            closing_resp = self.db.table("closing_lines").select("id").eq(
                "game_id", game_id
            ).limit(1).execute()
            if not (closing_resp.data or []):
                flags.append("NO_CLOSING_LINE")
        except Exception:
            flags.append("NO_CLOSING_LINE")
        return flags

    async def get_team_recommendation(self, team_abbrev: str) -> Dict[str, Any]:
        team = self._team_row(team_abbrev)
        if not team:
            return {
                "team": team_abbrev.upper(),
                "model_version": "v1-netrating-pace",
                "generated_at": datetime.utcnow().isoformat(),
                "next_game": None,
                "top_pick": None,
                "recommendations": [],
                "risk_flags": [],
            }

        team_name = team.get("full_name") or ""
        next_game = self._next_game(team_name)
        if not next_game:
            return {
                "team": team.get("abbreviation"),
                "model_version": "v1-netrating-pace",
                "generated_at": datetime.utcnow().isoformat(),
                "next_game": None,
                "top_pick": None,
                "recommendations": [],
                "risk_flags": [],
            }

        game_id = next_game.get("id")
        if not game_id:
            return {
                "team": team.get("abbreviation"),
                "model_version": "v1-netrating-pace",
                "generated_at": datetime.utcnow().isoformat(),
                "next_game": None,
                "top_pick": None,
                "recommendations": [],
                "risk_flags": [],
            }

        min_ev = float(os.getenv("MIN_EV", "0.02"))
        min_edge = float(os.getenv("MIN_EDGE", "0.03"))

        value_board = [
            row for row in self.value_service.get_value_board(window_days=2)
            if row.get("game_id") == game_id
        ]

        recommendations: List[Dict[str, Any]] = []
        for row in value_board:
            market = row.get("market_type")
            selection = row.get("selection")
            if not market:
                continue
            if market in {"spreads", "h2h"} and selection != team_name:
                continue

            reasons: List[str] = []
            details: Dict[str, Any] = {}

            odds_gate = await self.quality_gates.check_odds_availability(game_id, market)
            if not odds_gate.passed:
                reasons.extend([r.value for r in odds_gate.reasons])
                details.update({"odds": odds_gate.details})

            stats_gate = await self.quality_gates.check_stats_recency(team.get("abbreviation"))
            if not stats_gate.passed:
                reasons.extend([r.value for r in stats_gate.reasons])
                details.update({"stats": stats_gate.details})

            if row.get("ev") is not None and row.get("ev") < min_ev:
                reasons.append("EV_TOO_LOW")
            if row.get("edge_prob") is not None and row.get("edge_prob") < min_edge:
                reasons.append("EDGE_TOO_SMALL")

            model_prob = row.get("model_prob")
            edge = row.get("edge_prob")
            recommendations.append({
                "market": market,
                "selection": selection,
                "line": row.get("point"),
                "price": row.get("price"),
                "implied_prob": row.get("implied_prob"),
                "model_prob": model_prob,
                "edge": edge,
                "ev": row.get("ev"),
                "confidence": _confidence(edge, model_prob),
                "decision": "BET" if len(reasons) == 0 else "NO_BET",
                "reasons": reasons,
                "details": details,
                "why_bullets": row.get("why_bullets") or [],
            })

        recommendations.sort(key=lambda r: r.get("ev") or -999, reverse=True)
        top_pick = None
        for row in recommendations:
            if row.get("decision") == "BET":
                top_pick = row
                break
        if top_pick is None and recommendations:
            top_pick = recommendations[0]

        risk_flags = self._risk_flags(game_id)

        return {
            "team": team.get("abbreviation"),
            "model_version": "v1-netrating-pace",
            "generated_at": datetime.utcnow().isoformat(),
            "next_game": {
                "game_id": game_id,
                "commence_time": next_game.get("commence_time"),
                "home_team": next_game.get("home_team"),
                "away_team": next_game.get("away_team"),
                "is_home": team_name == next_game.get("home_team"),
                "opponent": next_game.get("away_team") if team_name == next_game.get("home_team") else next_game.get("home_team"),
            },
            "top_pick": top_pick,
            "recommendations": recommendations,
            "risk_flags": risk_flags,
        }


_ai_service: Optional[AIRecommendationService] = None


def get_ai_recommendation_service() -> AIRecommendationService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIRecommendationService()
    return _ai_service
