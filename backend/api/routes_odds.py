"""
Odds API routes.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from db import get_db
from models import OddsSnapshot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/odds", tags=["odds"])


@router.get("/{game_id}")
async def get_current_odds(
    game_id: str,
    market_type: Optional[str] = Query(None, description="Filter by market type (h2h, spreads, totals)")
):
    """
    Get current odds for a specific game.
    
    Args:
        game_id: Game identifier
        market_type: Optional market type filter
    
    Returns:
        Latest odds snapshots for the game grouped by bookmaker
    """
    try:
        db = get_db()
        
        # Get the most recent snapshot time for this game
        query = db.table("odds_snapshots").select("snapshot_time").eq(
            "game_id", game_id
        ).order("snapshot_time", desc=True).limit(1)
        
        if market_type:
            query = query.eq("market_type", market_type)
        
        latest_result = query.execute()
        
        if not latest_result.data:
            return JSONResponse(
                content={"game_id": game_id, "odds": [], "message": "No odds data available"},
                status_code=200
            )
        
        latest_time = latest_result.data[0]["snapshot_time"]
        
        # Get all odds from the latest snapshot
        odds_query = db.table("odds_snapshots").select("*").eq(
            "game_id", game_id
        ).eq("snapshot_time", latest_time)
        
        if market_type:
            odds_query = odds_query.eq("market_type", market_type)
        
        odds_result = odds_query.execute()
        
        return JSONResponse(
            content={
                "game_id": game_id,
                "snapshot_time": latest_time,
                "odds": odds_result.data if odds_result.data else []
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error fetching odds for game {game_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch odds: {str(e)}")


@router.get("/line-movement/{game_id}")
async def get_line_movement(
    game_id: str,
    market_type: str = Query(..., description="Market type (h2h, spreads, totals)"),
    bookmaker_key: Optional[str] = Query(None, description="Filter by specific bookmaker"),
    hours_back: int = Query(24, description="Hours of history to retrieve", ge=1, le=168)
):
    """
    Get line movement timeline for a game.
    
    Args:
        game_id: Game identifier
        market_type: Market type (h2h, spreads, totals)
        bookmaker_key: Optional bookmaker filter
        hours_back: Hours of history to retrieve (1-168)
    
    Returns:
        Timeline of odds changes over the specified period
    """
    try:
        db = get_db()
        
        # Calculate cutoff time
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Build query
        query = db.table("odds_snapshots").select("*").eq(
            "game_id", game_id
        ).eq(
            "market_type", market_type
        ).gte(
            "snapshot_time", cutoff.isoformat()
        ).order("snapshot_time", desc=False)
        
        if bookmaker_key:
            query = query.eq("bookmaker_key", bookmaker_key)
        
        result = query.execute()
        
        if not result.data:
            return JSONResponse(
                content={
                    "game_id": game_id,
                    "market_type": market_type,
                    "timeline": [],
                    "message": "No line movement data available"
                },
                status_code=200
            )
        
        # Group by bookmaker and outcome for easier visualization
        timeline_by_bookmaker = {}
        for snapshot in result.data:
            bookmaker = snapshot["bookmaker_key"]
            if bookmaker not in timeline_by_bookmaker:
                timeline_by_bookmaker[bookmaker] = []
            timeline_by_bookmaker[bookmaker].append(snapshot)
        
        return JSONResponse(
            content={
                "game_id": game_id,
                "market_type": market_type,
                "hours_back": hours_back,
                "timeline_by_bookmaker": timeline_by_bookmaker,
                "total_snapshots": len(result.data)
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error fetching line movement for game {game_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch line movement: {str(e)}")
