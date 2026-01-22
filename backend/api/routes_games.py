"""
Games API routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime, date, timedelta
import logging

from db import get_db
from models import Game

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/today", response_model=List[Game])
async def get_todays_games():
    """
    Get all games scheduled for today.
    
    Returns:
        List[Game]: Games with commence_time in the next 24 hours
    """
    try:
        db = get_db()
        
        # Get games for today (next 24 hours)
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        result = db.table("games").select("*").gte(
            "commence_time", now.isoformat()
        ).lte(
            "commence_time", tomorrow.isoformat()
        ).order("commence_time").execute()
        
        if not result.data:
            return []
        
        return result.data
    
    except Exception as e:
        logger.error(f"Error fetching today's games: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {str(e)}")
