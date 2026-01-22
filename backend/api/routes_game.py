"""
Game endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, date
from typing import List

from models import Game, GameStatus
from backend.supabase_client import create_isolated_supabase_client, get_supabase_config

router = APIRouter()


@router.get("/api/games/today", response_model=List[Game], tags=["games"])
async def get_todays_games():
    """
    Get all games scheduled for today.
    
    Returns:
        List[Game]: List of games scheduled for today
    """
    try:
        config = get_supabase_config()
        if not config["available"]:
            raise HTTPException(status_code=503, detail="Database not available")
        
        supabase = create_isolated_supabase_client(
            config["url"],
            config["service_key"] or config["anon_key"]
        )
        
        if not supabase:
            raise HTTPException(status_code=503, detail="Failed to connect to database")
        
        # Get today's date range
        today = date.today()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(today, datetime.max.time()).isoformat()
        
        # Query games for today
        result = supabase.table("games").select("*").gte(
            "commence_time", start_of_day
        ).lte(
            "commence_time", end_of_day
        ).order("commence_time").execute()
        
        games = []
        for game_data in result.data:
            games.append(Game(
                id=game_data["id"],
                home_team=game_data["home_team"],
                away_team=game_data["away_team"],
                commence_time=datetime.fromisoformat(game_data["commence_time"]),
                status=GameStatus(game_data.get("status", "scheduled")),
                nba_game_id=game_data.get("nba_game_id")
            ))
        
        return games
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get today's games: {str(e)}")
