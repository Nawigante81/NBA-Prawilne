"""
Closing Line Value (CLV) service for tracking line movements and calculating CLV.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from db import get_db
from services.betting_math import calculate_clv_spreads, calculate_clv_totals, calculate_clv_moneyline
import logging

logger = logging.getLogger(__name__)


class CLVService:
    """Service for managing closing line value calculations and line movement tracking."""
    
    def __init__(self):
        self.db = get_db()
    
    async def get_closing_line(
        self, 
        game_id: str, 
        market_type: str, 
        team: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get the closing line for a game/market.
        Closing line = last odds snapshot before game commence_time.
        
        Args:
            game_id: Game ID
            market_type: "h2h", "spreads", or "totals"
            team: Team name (for h2h and spreads)
        
        Returns:
            Dictionary with closing line info or None
        """
        # Get game commence time
        game_result = self.db.table("games").select("commence_time").eq("id", game_id).execute()
        
        if not game_result.data or len(game_result.data) == 0:
            logger.warning(f"Game {game_id} not found")
            return None
        
        commence_time = datetime.fromisoformat(game_result.data[0]["commence_time"].replace("Z", "+00:00"))
        
        # Query odds snapshots before commence time
        query = self.db.table("odds_snapshots").select("*").eq("game_id", game_id).eq("market_type", market_type).lt("snapshot_time", commence_time.isoformat())
        
        if team:
            query = query.eq("team", team)
        
        query = query.order("snapshot_time", desc=True).limit(1)
        
        result = query.execute()
        
        if not result.data or len(result.data) == 0:
            logger.warning(f"No closing line found for game {game_id}, market {market_type}, team {team}")
            return None
        
        return result.data[0]
    
    async def calculate_clv_for_pick(self, pick_id: str) -> Optional[float]:
        """
        Calculate CLV for a settled pick.
        
        Args:
            pick_id: Pick ID
        
        Returns:
            CLV value or None
        """
        # Get pick details
        pick_result = self.db.table("picks").select("*").eq("id", pick_id).execute()
        
        if not pick_result.data or len(pick_result.data) == 0:
            logger.warning(f"Pick {pick_id} not found")
            return None
        
        pick = pick_result.data[0]
        
        game_id = pick["game_id"]
        market_type = pick["market_type"]
        selection = pick["selection"]
        bet_odds = pick["odds"]
        bet_point = pick.get("point")
        
        # Get closing line
        closing = await self.get_closing_line(game_id, market_type, selection)
        
        if not closing:
            return None
        
        closing_odds = closing.get("price")
        closing_point = closing.get("point")
        
        # Calculate CLV based on market type
        if market_type == "h2h":
            clv_prob, clv_price = calculate_clv_moneyline(bet_odds, closing_odds, "american")
            return clv_prob  # Use probability delta
        
        elif market_type == "spreads":
            if bet_point is None or closing_point is None:
                return None
            is_favorite = bet_point < 0
            return calculate_clv_spreads(bet_point, closing_point, is_favorite)
        
        elif market_type == "totals":
            if bet_point is None or closing_point is None:
                return None
            is_over = "over" in selection.lower()
            return calculate_clv_totals(bet_point, closing_point, is_over)
        
        return None
    
    async def get_line_movement(
        self, 
        game_id: str, 
        market_type: str, 
        team: Optional[str] = None,
        bookmaker: Optional[str] = None
    ) -> List[Dict]:
        """
        Get line movement timeline for a game/market.
        
        Args:
            game_id: Game ID
            market_type: "h2h", "spreads", or "totals"
            team: Team name (optional)
            bookmaker: Bookmaker key (optional)
        
        Returns:
            List of snapshots ordered by time: [{"ts": ..., "line": ..., "price": ...}, ...]
        """
        query = self.db.table("odds_snapshots").select("snapshot_time, point, price, bookmaker_key").eq("game_id", game_id).eq("market_type", market_type)
        
        if team:
            query = query.eq("team", team)
        
        if bookmaker:
            query = query.eq("bookmaker_key", bookmaker)
        
        query = query.order("snapshot_time", desc=False)
        
        result = query.execute()
        
        if not result.data:
            return []
        
        timeline = []
        for snapshot in result.data:
            timeline.append({
                "ts": snapshot["snapshot_time"],
                "line": snapshot.get("point"),
                "price": snapshot.get("price"),
                "bookmaker": snapshot.get("bookmaker_key")
            })
        
        return timeline
    
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
        content_hash: Optional[str] = None
    ) -> bool:
        """
        Store an odds snapshot with deduplication.
        
        Returns:
            True if stored, False if duplicate
        """
        # Check if duplicate exists (same content_hash within last 6 hours)
        if content_hash:
            six_hours_ago = snapshot_time - timedelta(hours=6)
            existing = self.db.table("odds_snapshots").select("id").eq("game_id", game_id).eq("market_type", market_type).eq("content_hash", content_hash).gte("snapshot_time", six_hours_ago.isoformat()).execute()
            
            if existing.data and len(existing.data) > 0:
                logger.debug(f"Duplicate snapshot detected, skipping")
                return False
        
        # Insert new snapshot
        self.db.table("odds_snapshots").insert({
            "game_id": game_id,
            "bookmaker_key": bookmaker_key,
            "bookmaker_title": bookmaker_title,
            "market_type": market_type,
            "outcome_name": outcome_name,
            "team": team,
            "point": point,
            "price": price,
            "snapshot_time": snapshot_time.isoformat(),
            "content_hash": content_hash
        }).execute()
        
        logger.info(f"Stored odds snapshot for {game_id} {market_type}")
        return True
    
    async def get_clv_summary(self, start_date: Optional[datetime] = None) -> Dict:
        """
        Get summary of CLV performance.
        
        Args:
            start_date: Start date for summary (default: 30 days ago)
        
        Returns:
            Dictionary with CLV statistics
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Query pick results with CLV
        result = self.db.table("pick_results").select("clv, status").gte("settled_at", start_date.isoformat()).execute()
        
        if not result.data:
            return {
                "total_picks": 0,
                "avg_clv": 0,
                "positive_clv_count": 0,
                "negative_clv_count": 0
            }
        
        clv_values = [r.get("clv", 0) for r in result.data if r.get("clv") is not None]
        
        if not clv_values:
            return {
                "total_picks": len(result.data),
                "avg_clv": 0,
                "positive_clv_count": 0,
                "negative_clv_count": 0
            }
        
        avg_clv = sum(clv_values) / len(clv_values)
        positive_count = sum(1 for v in clv_values if v > 0)
        negative_count = sum(1 for v in clv_values if v < 0)
        
        return {
            "total_picks": len(result.data),
            "avg_clv": avg_clv,
            "positive_clv_count": positive_count,
            "negative_clv_count": negative_count,
            "positive_clv_rate": positive_count / len(clv_values) if clv_values else 0
        }


# Global instance
_clv_service: Optional[CLVService] = None


def get_clv_service() -> CLVService:
    """Get or create CLV service singleton."""
    global _clv_service
    if _clv_service is None:
        _clv_service = CLVService()
    return _clv_service
