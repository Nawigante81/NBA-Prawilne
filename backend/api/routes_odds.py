"""
Odds endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import GameOdds, OddsMovement, CLVData, ConsensusLine, MarketType
from services.odds_service import get_current_odds, get_odds_movement, get_consensus_line
from services.clv_service import get_closing_line

router = APIRouter()


@router.get("/api/game/{game_id}/odds/current", response_model=List[GameOdds], tags=["odds"])
async def get_game_current_odds(game_id: str):
    """
    Get current odds for a specific game from all bookmakers.
    
    Args:
        game_id: Unique game identifier
    
    Returns:
        List[GameOdds]: Current odds from all bookmakers
    """
    try:
        odds = await get_current_odds(game_id)
        
        if not odds:
            raise HTTPException(status_code=404, detail=f"No odds found for game '{game_id}'")
        
        return odds
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current odds: {str(e)}")


@router.get("/api/game/{game_id}/odds/movement", response_model=OddsMovement, tags=["odds"])
async def get_game_odds_movement(
    game_id: str,
    market_type: MarketType = Query(..., description="Market type (h2h, spread, totals)"),
    team: Optional[str] = Query(None, description="Team abbreviation (required for h2h and spread)")
):
    """
    Get odds movement over time for a specific market.
    
    Args:
        game_id: Unique game identifier
        market_type: Type of market (h2h, spread, totals)
        team: Team abbreviation for h2h and spread markets
    
    Returns:
        OddsMovement: Historical odds movement data
    """
    try:
        if market_type in [MarketType.H2H, MarketType.SPREAD] and not team:
            raise HTTPException(status_code=400, detail="Team parameter required for h2h and spread markets")
        
        movement = await get_odds_movement(game_id, market_type.value, team)
        
        if not movement:
            raise HTTPException(
                status_code=404,
                detail=f"No odds movement found for game '{game_id}', market '{market_type}'"
            )
        
        return movement
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get odds movement: {str(e)}")


@router.get("/api/game/{game_id}/clv", response_model=CLVData, tags=["odds"])
async def get_game_clv(
    game_id: str,
    market_type: MarketType = Query(..., description="Market type (h2h, spread, totals)"),
    team: Optional[str] = Query(None, description="Team abbreviation (required for h2h and spread)")
):
    """
    Get Closing Line Value (CLV) data for a game.
    
    Args:
        game_id: Unique game identifier
        market_type: Type of market (h2h, spread, totals)
        team: Team abbreviation for h2h and spread markets
    
    Returns:
        CLVData: Closing line value information
    """
    try:
        if market_type in [MarketType.H2H, MarketType.SPREAD] and not team:
            raise HTTPException(status_code=400, detail="Team parameter required for h2h and spread markets")
        
        clv_data = await get_closing_line(game_id, market_type.value, team)
        
        if not clv_data:
            raise HTTPException(
                status_code=404,
                detail=f"No CLV data found for game '{game_id}', market '{market_type}'"
            )
        
        return clv_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get CLV data: {str(e)}")


@router.get("/api/game/{game_id}/consensus", response_model=ConsensusLine, tags=["odds"])
async def get_game_consensus(
    game_id: str,
    market_type: MarketType = Query(..., description="Market type (h2h, spread, totals)"),
    team: Optional[str] = Query(None, description="Team abbreviation (required for h2h and spread)"),
    cutoff: str = Query(default="now", description="Time cutoff: 'now' or 'closing'")
):
    """
    Get consensus line from multiple bookmakers.
    
    Args:
        game_id: Unique game identifier
        market_type: Type of market (h2h, spread, totals)
        team: Team abbreviation for h2h and spread markets
        cutoff: Time cutoff - 'now' for current or 'closing' for closing line
    
    Returns:
        ConsensusLine: Consensus line from multiple bookmakers
    """
    try:
        if market_type in [MarketType.H2H, MarketType.SPREAD] and not team:
            raise HTTPException(status_code=400, detail="Team parameter required for h2h and spread markets")
        
        if cutoff not in ["now", "closing"]:
            raise HTTPException(status_code=400, detail="Cutoff must be 'now' or 'closing'")
        
        cutoff_time = "closing" if cutoff == "closing" else None
        
        consensus = await get_consensus_line(game_id, market_type.value, team, cutoff_time)
        
        if not consensus:
            raise HTTPException(
                status_code=404,
                detail=f"No consensus line found for game '{game_id}', market '{market_type}'"
            )
        
        return consensus
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get consensus line: {str(e)}")
