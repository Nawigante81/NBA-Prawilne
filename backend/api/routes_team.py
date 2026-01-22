"""
Team endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import List, Optional

from models import TeamBettingStats, TeamNextGame, KeyPlayer, PlayerStatus
from services.betting_stats_service import get_team_ats_stats, get_team_ou_stats
from backend.supabase_client import create_isolated_supabase_client, get_supabase_config

router = APIRouter()


@router.get("/api/team/{abbrev}/betting-stats", response_model=TeamBettingStats, tags=["team"])
async def get_team_betting_stats(
    abbrev: str,
    window: int = Query(default=20, ge=1, le=82, description="Number of games to analyze")
):
    """
    Get team betting statistics over a rolling window.
    
    Args:
        abbrev: Team abbreviation (e.g., 'LAL', 'BOS')
        window: Number of recent games to analyze (default: 20)
    
    Returns:
        TeamBettingStats: ATS and O/U betting statistics
    """
    try:
        # Get ATS stats
        ats_stats = await get_team_ats_stats(abbrev, window)
        
        # Get O/U stats
        ou_stats = await get_team_ou_stats(abbrev, window)
        
        if not ats_stats or not ou_stats:
            raise HTTPException(status_code=404, detail=f"Team '{abbrev}' not found or insufficient data")
        
        return TeamBettingStats(
            team_abbrev=abbrev.upper(),
            window=window,
            ats_record=ats_stats["record"],
            ats_win_pct=ats_stats["win_pct"],
            ats_roi=ats_stats["roi"],
            avg_spread_diff=ats_stats["avg_spread_diff"],
            ou_record=ou_stats["record"],
            over_pct=ou_stats["over_pct"],
            avg_total_diff=ou_stats["avg_total_diff"],
            avg_total_points=ou_stats["avg_total_points"],
            games_analyzed=min(ats_stats["games_analyzed"], ou_stats["games_analyzed"]),
            last_updated=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get betting stats: {str(e)}")


@router.get("/api/team/{abbrev}/next-game", response_model=TeamNextGame, tags=["team"])
async def get_team_next_game(abbrev: str):
    """
    Get the next scheduled game for a team.
    
    Args:
        abbrev: Team abbreviation (e.g., 'LAL', 'BOS')
    
    Returns:
        TeamNextGame: Next game information
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
        
        abbrev_upper = abbrev.upper()
        now = datetime.utcnow().isoformat()
        
        # Query for next game
        result = supabase.table("games").select("*").or_(
            f"home_team.eq.{abbrev_upper},away_team.eq.{abbrev_upper}"
        ).gte("commence_time", now).order("commence_time").limit(1).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No upcoming game found for team '{abbrev}'")
        
        game = result.data[0]
        is_home = game["home_team"] == abbrev_upper
        opponent = game["away_team"] if is_home else game["home_team"]
        
        # Check if odds are available
        odds_result = supabase.table("odds").select("id").eq("game_id", game["id"]).limit(1).execute()
        odds_available = len(odds_result.data) > 0
        
        return TeamNextGame(
            game_id=game["id"],
            opponent=opponent,
            is_home=is_home,
            commence_time=datetime.fromisoformat(game["commence_time"]),
            odds_available=odds_available
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get next game: {str(e)}")


@router.get("/api/team/{abbrev}/key-players", response_model=List[KeyPlayer], tags=["team"])
async def get_team_key_players(abbrev: str):
    """
    Get key players for a team based on recent playing time.
    
    Args:
        abbrev: Team abbreviation (e.g., 'LAL', 'BOS')
    
    Returns:
        List[KeyPlayer]: Top 3 players by minutes with trend analysis
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
        
        abbrev_upper = abbrev.upper()
        
        # Get recent player stats for the team (last 5 games per player)
        result = supabase.table("player_game_stats").select(
            "player_id, player_name, position, minutes, game_date"
        ).eq("team_abbrev", abbrev_upper).order("game_date", desc=True).limit(100).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"No player data found for team '{abbrev}'")
        
        # Group by player and calculate averages
        from collections import defaultdict
        player_data = defaultdict(list)
        
        for stat in result.data:
            if stat["minutes"] and stat["minutes"] > 0:
                player_data[stat["player_id"]].append({
                    "name": stat["player_name"],
                    "position": stat.get("position"),
                    "minutes": float(stat["minutes"]),
                    "game_date": stat["game_date"]
                })
        
        # Calculate averages and trends for each player
        key_players = []
        for player_id, games in player_data.items():
            # Sort by date and take last 5 games
            games_sorted = sorted(games, key=lambda x: x["game_date"], reverse=True)[:5]
            
            if len(games_sorted) < 3:  # Need at least 3 games
                continue
            
            avg_minutes = sum(g["minutes"] for g in games_sorted) / len(games_sorted)
            
            # Calculate trend (compare first 2 vs last 2 games)
            if len(games_sorted) >= 4:
                recent_avg = sum(g["minutes"] for g in games_sorted[:2]) / 2
                older_avg = sum(g["minutes"] for g in games_sorted[2:4]) / 2
                diff = recent_avg - older_avg
                
                if diff > 3:
                    trend = "UP"
                elif diff < -3:
                    trend = "DOWN"
                else:
                    trend = "STABLE"
            else:
                trend = "STABLE"
            
            key_players.append(KeyPlayer(
                player_id=player_id,
                name=games_sorted[0]["name"],
                position=games_sorted[0]["position"],
                avg_minutes=round(avg_minutes, 1),
                minutes_trend=trend,
                status=PlayerStatus.ACTIVE,
                games_played=len(games_sorted)
            ))
        
        # Sort by average minutes and return top 3
        key_players.sort(key=lambda x: x.avg_minutes, reverse=True)
        
        if not key_players:
            raise HTTPException(status_code=404, detail=f"No qualifying players found for team '{abbrev}'")
        
        return key_players[:3]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get key players: {str(e)}")
