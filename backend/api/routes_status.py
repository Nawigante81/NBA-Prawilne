"""
System status endpoint
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

from models import SystemStatus
from backend.supabase_client import create_isolated_supabase_client, get_supabase_config

router = APIRouter()


async def check_database_connection() -> bool:
    """Check if database is accessible"""
    try:
        config = get_supabase_config()
        if not config["available"]:
            return False
        
        supabase = create_isolated_supabase_client(
            config["url"],
            config["service_key"] or config["anon_key"]
        )
        
        if not supabase:
            return False
        
        # Simple query to verify connection
        result = supabase.table("games").select("id").limit(1).execute()
        return True
    except Exception:
        return False


async def get_odds_api_budget() -> dict:
    """Get current Odds API budget info"""
    # TODO: Implement actual budget tracking
    return {
        "used": 0,
        "remaining": 500,
        "total": 500,
        "reset_date": None
    }


async def get_last_sync_times() -> tuple[Optional[datetime], Optional[datetime]]:
    """Get last sync timestamps for NBA stats and odds"""
    try:
        config = get_supabase_config()
        if not config["available"]:
            return None, None
        
        supabase = create_isolated_supabase_client(
            config["url"],
            config["service_key"] or config["anon_key"]
        )
        
        if not supabase:
            return None, None
        
        # Get last NBA stats sync
        nba_result = supabase.table("player_game_stats").select("created_at").order("created_at", desc=True).limit(1).execute()
        last_nba_sync = datetime.fromisoformat(nba_result.data[0]["created_at"]) if nba_result.data else None
        
        # Get last odds sync
        odds_result = supabase.table("odds").select("created_at").order("created_at", desc=True).limit(1).execute()
        last_odds_sync = datetime.fromisoformat(odds_result.data[0]["created_at"]) if odds_result.data else None
        
        return last_nba_sync, last_odds_sync
    except Exception:
        return None, None


async def get_cached_games_count() -> int:
    """Get count of games in cache"""
    try:
        config = get_supabase_config()
        if not config["available"]:
            return 0
        
        supabase = create_isolated_supabase_client(
            config["url"],
            config["service_key"] or config["anon_key"]
        )
        
        if not supabase:
            return 0
        
        result = supabase.table("games").select("id", count="exact").execute()
        return result.count or 0
    except Exception:
        return 0


@router.get("/api/status", response_model=SystemStatus, tags=["status"])
async def get_system_status():
    """
    Get comprehensive system status including database, API budget, and sync times.
    
    Returns:
        SystemStatus: System health and operational metrics
    """
    try:
        db_status = await check_database_connection()
        odds_budget = await get_odds_api_budget()
        last_nba_sync, last_odds_sync = await get_last_sync_times()
        games_count = await get_cached_games_count()
        
        return SystemStatus(
            status="healthy" if db_status else "degraded",
            timestamp=datetime.utcnow(),
            database=db_status,
            odds_api_budget=odds_budget,
            last_sync_nba_stats=last_nba_sync,
            last_sync_odds=last_odds_sync,
            cached_games_count=games_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")
