"""
Teams API routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime
import logging

from db import get_db
from models import Team

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=List[Team])
async def get_teams():
    """
    Get all NBA teams.
    
    Returns:
        List[Team]: All teams in the database
    """
    try:
        db = get_db()
        result = db.table("teams").select("*").order("full_name").execute()
        
        if not result.data:
            return []
        
        return result.data
    
    except Exception as e:
        logger.error(f"Error fetching teams: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch teams: {str(e)}")
