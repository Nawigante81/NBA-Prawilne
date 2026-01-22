"""
Odds consensus and snapshot utilities.
"""
from __future__ import annotations

from datetime import datetime
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple

from db import get_db
from settings import settings
from services.betting_math import implied_probability
import logging

logger = logging.getLogger(__name__)


def normalize_market_type(value: str | None) -> str:
    val = (value or "").strip().lower()
    if val in ["spread", "spreads"]:
        return "spreads"
    if val in ["total", "totals"]:
        return "totals"
    if val in ["h2h", "moneyline", "ml"]:
        return "h2h"
    return val


def _parse_ts(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return float(median(values))


def _mad_filter(points: List[float]) -> Tuple[List[float], int]:
    if len(points) < 3:
        return points, 0
    med = _median(points)
    if med is None:
        return points, 0
    abs_dev = [abs(x - med) for x in points]
    mad = _median(abs_dev) or 0.0
    threshold = max(0.5, 3 * mad)
    filtered = [x for x in points if abs(x - med) <= threshold]
    return filtered, max(0, len(points) - len(filtered))


def _closest_point(points: List[float], target: float) -> Optional[float]:
    if not points:
        return None
    return min(points, key=lambda x: abs(x - target))


def _select_price_for_point(samples: List[Dict[str, Any]], consensus_point: float | None) -> Optional[float]:
    if not samples:
        return None
    if consensus_point is None:
        return None
    exact = [s for s in samples if s.get("point") == consensus_point and s.get("price") is not None]
    if exact:
        return _median([float(s.get("price")) for s in exact])
    candidates = [s for s in samples if s.get("price") is not None and s.get("point") is not None]
    if not candidates:
        return None
    closest = min(candidates, key=lambda r: abs(float(r.get("point")) - consensus_point))
    return float(closest.get("price"))


def _allowlist() -> List[str]:
    allowlist = [b.strip() for b in settings.odds_bookmakers_allowlist if b.strip()]
    return allowlist[:3]


class OddsService:
    """Consensus odds and closing line utilities."""

    def __init__(self):
        self.db = get_db()

    def _latest_per_bookmaker(
        self,
        rows: Iterable[Dict[str, Any]],
        cutoff: Optional[datetime],
    ) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            ts_val = _parse_ts(row.get("ts"))
            if not ts_val:
                continue
            if cutoff and ts_val > cutoff:
                continue
            book = row.get("bookmaker_key")
            if not book:
                continue
            existing = latest.get(book)
            if not existing:
                latest[book] = {**row, "_ts": ts_val}
                continue
            if ts_val > existing.get("_ts"):
                latest[book] = {**row, "_ts": ts_val}
        return latest

    def _fetch_snapshots(self, game_id: str, market_type: str) -> List[Dict[str, Any]]:
        allowlist = _allowlist()
        normalized = normalize_market_type(market_type)
        market_types = [normalized]
        if normalized == "spreads":
            market_types.append("spread")
        if normalized == "totals":
            market_types.append("total")
        query = self.db.table("odds_snapshots").select(
            "game_id,bookmaker_key,market_type,outcome_name,team,point,price,ts"
        ).eq("game_id", game_id).in_("market_type", market_types)
        if allowlist:
            query = query.in_("bookmaker_key", allowlist)
        result = query.execute()
        return result.data or []

    def consensus_spread(
        self,
        game_id: str,
        team: str,
        cutoff: Optional[datetime],
    ) -> Dict[str, Any]:
        rows = [r for r in self._fetch_snapshots(game_id, "spreads") if r.get("team") == team]
        by_book = self._latest_per_bookmaker(rows, cutoff)
        points = [float(r.get("point")) for r in by_book.values() if r.get("point") is not None]
        filtered, outliers_removed = _mad_filter(points)
        consensus_point = _median(filtered)
        if consensus_point is not None:
            consensus_point = _closest_point(filtered, consensus_point)

        prices = [r for r in by_book.values() if r.get("price") is not None]
        consensus_price = _select_price_for_point(prices, consensus_point)

        used_bookmakers = [r.get("bookmaker_key") for r in by_book.values() if r.get("bookmaker_key")]

        return {
            "market_type": "spreads",
            "team": team,
            "point": consensus_point,
            "price": consensus_price,
            "implied_prob": implied_probability(consensus_price, "american") if consensus_price else None,
            "sample_count": len(filtered),
            "used_bookmakers": used_bookmakers,
            "outliers_removed": outliers_removed,
            "method": "consensus_median_mad",
        }

    def consensus_totals(
        self,
        game_id: str,
        cutoff: Optional[datetime],
    ) -> Dict[str, Any]:
        rows = self._fetch_snapshots(game_id, "totals")
        by_book_over = self._latest_per_bookmaker(
            [r for r in rows if (r.get("outcome_name") or "").lower() == "over"],
            cutoff,
        )
        points = [float(r.get("point")) for r in by_book_over.values() if r.get("point") is not None]
        filtered, outliers_removed = _mad_filter(points)
        consensus_point = _median(filtered)
        if consensus_point is not None:
            consensus_point = _closest_point(filtered, consensus_point)

        def _price_for_outcome(outcome: str) -> Optional[float]:
            by_book = self._latest_per_bookmaker(
                [r for r in rows if (r.get("outcome_name") or "").lower() == outcome],
                cutoff,
            )
            candidates = [r for r in by_book.values() if r.get("price") is not None]
            return _select_price_for_point(candidates, consensus_point)

        over_price = _price_for_outcome("over")
        under_price = _price_for_outcome("under")
        used_bookmakers = [r.get("bookmaker_key") for r in by_book_over.values() if r.get("bookmaker_key")]

        return {
            "market_type": "totals",
            "point": consensus_point,
            "over": {
                "team": "Over",
                "price": over_price,
                "implied_prob": implied_probability(over_price, "american") if over_price else None,
            },
            "under": {
                "team": "Under",
                "price": under_price,
                "implied_prob": implied_probability(under_price, "american") if under_price else None,
            },
            "sample_count": len(filtered),
            "used_bookmakers": used_bookmakers,
            "outliers_removed": outliers_removed,
            "method": "consensus_median_mad",
        }

    def consensus_h2h(
        self,
        game_id: str,
        team: str,
        cutoff: Optional[datetime],
    ) -> Dict[str, Any]:
        rows = [r for r in self._fetch_snapshots(game_id, "h2h") if r.get("team") == team]
        by_book = self._latest_per_bookmaker(rows, cutoff)
        prices = [float(r.get("price")) for r in by_book.values() if r.get("price") is not None]
        consensus_price = _median(prices)
        used_bookmakers = [r.get("bookmaker_key") for r in by_book.values() if r.get("bookmaker_key")]

        return {
            "market_type": "h2h",
            "team": team,
            "price": consensus_price,
            "implied_prob": implied_probability(consensus_price, "american") if consensus_price else None,
            "sample_count": len(prices),
            "used_bookmakers": used_bookmakers,
            "outliers_removed": 0,
            "method": "consensus_median_mad",
        }

    def consensus_for_game(self, game: Dict[str, Any], cutoff: Optional[datetime]) -> Dict[str, Any]:
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        return {
            "game_id": game.get("id"),
            "cutoff": cutoff.isoformat() if cutoff else None,
            "spreads": {
                "home": self.consensus_spread(game["id"], home_team, cutoff) if home_team else None,
                "away": self.consensus_spread(game["id"], away_team, cutoff) if away_team else None,
            },
            "totals": self.consensus_totals(game["id"], cutoff),
            "h2h": {
                "home": self.consensus_h2h(game["id"], home_team, cutoff) if home_team else None,
                "away": self.consensus_h2h(game["id"], away_team, cutoff) if away_team else None,
            },
        }

    def upsert_closing_lines(self, game: Dict[str, Any], consensus: Dict[str, Any]) -> None:
        game_id = game.get("id")
        if not game_id:
            return
        cutoff = game.get("commence_time")
        if not cutoff:
            return

        def _store_line(entry: Dict[str, Any]) -> None:
            if not entry:
                return
            if not entry.get("sample_count"):
                return
            payload = {
                "game_id": game_id,
                "market_type": entry.get("market_type"),
                "team": entry.get("team"),
                "point": entry.get("point"),
                "price": entry.get("price"),
                "ts_cutoff": cutoff,
                "method": entry.get("method"),
                "sample_count": entry.get("sample_count"),
                "used_bookmakers": entry.get("used_bookmakers"),
            }
            self.db.table("closing_lines").upsert(payload, on_conflict="game_id,market_type,team").execute()

        spreads = consensus.get("spreads") or {}
        _store_line(spreads.get("home"))
        _store_line(spreads.get("away"))

        totals = consensus.get("totals") or {}
        if totals:
            _store_line({
                "market_type": "totals",
                "team": "Over",
                "point": totals.get("point"),
                "price": (totals.get("over") or {}).get("price"),
                "method": totals.get("method"),
                "sample_count": totals.get("sample_count"),
                "used_bookmakers": totals.get("used_bookmakers"),
            })
            _store_line({
                "market_type": "totals",
                "team": "Under",
                "point": totals.get("point"),
                "price": (totals.get("under") or {}).get("price"),
                "method": totals.get("method"),
                "sample_count": totals.get("sample_count"),
                "used_bookmakers": totals.get("used_bookmakers"),
            })

        h2h = consensus.get("h2h") or {}
        _store_line(h2h.get("home"))
        _store_line(h2h.get("away"))


_odds_service: Optional[OddsService] = None


def get_odds_service() -> OddsService:
    global _odds_service
    if _odds_service is None:
        _odds_service = OddsService()
    return _odds_service
