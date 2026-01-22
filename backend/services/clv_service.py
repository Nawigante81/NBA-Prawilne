"""
Closing Line Value (CLV) service for tracking line movements and calculating CLV.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from db import get_db
from services.betting_math import calculate_clv_spreads, calculate_clv_totals, calculate_clv_moneyline
from services.odds_service import get_odds_service, normalize_market_type
from settings import settings
import logging

logger = logging.getLogger(__name__)


def _parse_ts(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


class CLVService:
    """Service for managing closing line value calculations and line movement tracking."""

    def __init__(self):
        self.db = get_db()
        self.odds_service = get_odds_service()

    async def get_closing_line(
        self,
        game_id: str,
        market_type: str,
        team: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get stored closing line, compute if missing."""
        normalized = normalize_market_type(market_type)
        query = self.db.table("closing_lines").select("*").eq("game_id", game_id).eq("market_type", normalized)
        if team is not None:
            query = query.eq("team", team)
        result = query.execute()
        if result.data:
            return result.data[0]

        game_result = self.db.table("games").select("id,commence_time,home_team,away_team").eq("id", game_id).execute()
        if not game_result.data:
            return None
        game = game_result.data[0]
        commence_time = game.get("commence_time")
        if not commence_time:
            return None

        cutoff_dt = _parse_ts(commence_time)
        consensus = self.odds_service.consensus_for_game(game, cutoff_dt)
        self.odds_service.upsert_closing_lines(game, consensus)

        # Retry after insert
        result = query.execute()
        if result.data:
            return result.data[0]
        return None

    async def get_clv_for_game(self, game_id: str) -> Dict[str, Any]:
        """Return CLV comparison of current consensus vs closing line."""
        game_result = self.db.table("games").select("id,commence_time,home_team,away_team").eq("id", game_id).execute()
        if not game_result.data:
            return {"game_id": game_id, "error": "Game not found"}
        game = game_result.data[0]
        cutoff_dt = _parse_ts(game.get("commence_time"))
        current = self.odds_service.consensus_for_game(game, None)
        closing = self.odds_service.consensus_for_game(game, cutoff_dt) if cutoff_dt else None

        def _clv_spread(team: str, current_line: Dict[str, Any], closing_line: Dict[str, Any]) -> Optional[float]:
            if not current_line or not closing_line:
                return None
            if current_line.get("point") is None or closing_line.get("point") is None:
                return None
            is_favorite = (current_line.get("point") or 0) < 0
            return calculate_clv_spreads(float(current_line["point"]), float(closing_line["point"]), is_favorite)

        def _clv_total(current_line: Dict[str, Any], closing_line: Dict[str, Any], is_over: bool) -> Optional[float]:
            if not current_line or not closing_line:
                return None
            if current_line.get("point") is None or closing_line.get("point") is None:
                return None
            return calculate_clv_totals(float(current_line["point"]), float(closing_line["point"]), is_over)

        def _clv_h2h(current_line: Dict[str, Any], closing_line: Dict[str, Any]) -> Optional[float]:
            if not current_line or not closing_line:
                return None
            if current_line.get("price") is None or closing_line.get("price") is None:
                return None
            clv_prob, _ = calculate_clv_moneyline(float(current_line["price"]), float(closing_line["price"]), "american")
            return clv_prob

        return {
            "game_id": game_id,
            "current": current,
            "closing": closing,
            "clv": {
                "spreads": {
                    "home": _clv_spread(game.get("home_team"), (current.get("spreads") or {}).get("home"), (closing.get("spreads") or {}).get("home")) if closing else None,
                    "away": _clv_spread(game.get("away_team"), (current.get("spreads") or {}).get("away"), (closing.get("spreads") or {}).get("away")) if closing else None,
                },
                "totals": {
                    "over": _clv_total(current.get("totals"), closing.get("totals"), True) if closing else None,
                    "under": _clv_total(current.get("totals"), closing.get("totals"), False) if closing else None,
                },
                "h2h": {
                    "home": _clv_h2h((current.get("h2h") or {}).get("home"), (closing.get("h2h") or {}).get("home")) if closing else None,
                    "away": _clv_h2h((current.get("h2h") or {}).get("away"), (closing.get("h2h") or {}).get("away")) if closing else None,
                },
            },
        }

    async def calculate_clv_for_pick(self, pick_id: str) -> Optional[float]:
        """Calculate CLV for a pick based on closing line."""
        pick_result = self.db.table("picks").select("*").eq("id", pick_id).execute()
        if not pick_result.data:
            return None
        pick = pick_result.data[0]
        market_type = pick.get("market_type")
        selection = pick.get("selection")
        bet_odds = pick.get("odds")
        bet_point = pick.get("point")

        closing = await self.get_closing_line(pick.get("game_id"), market_type, selection)
        if not closing:
            return None
        closing_odds = closing.get("price")
        closing_point = closing.get("point")

        normalized = normalize_market_type(market_type)
        if normalized == "h2h":
            if closing_odds is None or bet_odds is None:
                return None
            clv_prob, _ = calculate_clv_moneyline(float(bet_odds), float(closing_odds), "american")
            return clv_prob
        if normalized == "spreads":
            if closing_point is None or bet_point is None:
                return None
            is_favorite = float(bet_point) < 0
            return calculate_clv_spreads(float(bet_point), float(closing_point), is_favorite)
        if normalized == "totals":
            if closing_point is None or bet_point is None:
                return None
            is_over = "over" in str(selection).lower()
            return calculate_clv_totals(float(bet_point), float(closing_point), is_over)
        return None

    async def store_odds_snapshot(
        self,
        game_id: str,
        bookmaker_key: str,
        bookmaker_title: str,
        market_type: str,
        outcome_name: Optional[str],
        team: Optional[str],
        point: Optional[float],
        price: Optional[float],
        snapshot_time: datetime,
        content_hash: Optional[str] = None,
    ) -> bool:
        """Store snapshot with dedupe (change or every 6h)."""
        dedupe_hours = int(getattr(settings, "odds_snapshot_dedupe_hours", 6))
        six_hours_ago = snapshot_time - timedelta(hours=dedupe_hours)

        normalized = normalize_market_type(market_type)
        query = self.db.table("odds_snapshots").select("id,content_hash,point,price,ts").eq(
            "game_id", game_id
        ).eq("market_type", normalized).eq("bookmaker_key", bookmaker_key)

        if outcome_name:
            query = query.eq("outcome_name", outcome_name)
        if team:
            query = query.eq("team", team)

        query = query.order("ts", desc=True).limit(1)
        existing = query.execute()

        if existing.data:
            last = existing.data[0]
            last_ts = _parse_ts(last.get("ts"))
            if last_ts and last_ts >= six_hours_ago:
                if content_hash and last.get("content_hash") == content_hash:
                    return False
                if content_hash is None and last.get("point") == point and last.get("price") == price:
                    return False

        self.db.table("odds_snapshots").insert({
            "game_id": game_id,
            "bookmaker_key": bookmaker_key,
            "bookmaker_title": bookmaker_title,
            "market_type": normalized,
            "outcome_name": outcome_name,
            "team": team,
            "point": point,
            "price": price,
            "ts": snapshot_time.isoformat(),
            "content_hash": content_hash,
        }).execute()

        return True


_clv_service: Optional[CLVService] = None


def get_clv_service() -> CLVService:
    """Get or create CLV service singleton."""
    global _clv_service
    if _clv_service is None:
        _clv_service = CLVService()
    return _clv_service
