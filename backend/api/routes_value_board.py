"""
Value Board API routes.
Shows betting opportunities that pass quality gates.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging

from db import get_db
from services.quality_gates import QualityGateService
from services.betting_math import expected_value, american_to_decimal, implied_probability
from models import QualityGateResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/value-board", tags=["value-board"])


@router.get("/today")
async def get_value_board_today(
    min_ev: float = Query(0.03, description="Minimum expected value (default 3%)", ge=0.0),
    min_edge: float = Query(0.02, description="Minimum edge (default 2%)", ge=0.0),
    market_types: Optional[str] = Query(None, description="Comma-separated market types (h2h,spreads,totals)")
):
    """
    Get value bets for today that pass quality gates.
    
    Applies quality gate checks:
    - Odds availability and recency
    - Minimum EV and edge requirements
    - Data quality checks
    
    Args:
        min_ev: Minimum expected value threshold
        min_edge: Minimum edge threshold
        market_types: Optional filter for market types
    
    Returns:
        List of value opportunities with quality gate status
    """
    try:
        db = get_db()
        quality_gates = QualityGateService()
        
        # Get today's games
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        games_result = db.table("games").select("*").gte(
            "commence_time", now.isoformat()
        ).lte(
            "commence_time", tomorrow.isoformat()
        ).order("commence_time").execute()
        
        if not games_result.data:
            return JSONResponse(
                content={"value_bets": [], "message": "No games today"},
                status_code=200
            )
        
        value_bets = []
        market_type_list = market_types.split(",") if market_types else ["h2h", "spreads", "totals"]
        
        for game in games_result.data:
            game_id = game["id"]
            
            for market_type in market_type_list:
                # Check quality gates for this game/market
                gate_result = await quality_gates.check_odds_availability(game_id, market_type)
                
                if not gate_result.passed:
                    logger.debug(f"Game {game_id} market {market_type} failed quality gates: {gate_result.reasons}")
                    continue
                
                # Get latest odds for this market
                odds_result = db.table("odds_snapshots").select("*").eq(
                    "game_id", game_id
                ).eq(
                    "market_type", market_type
                ).order("snapshot_time", desc=True).limit(20).execute()
                
                if not odds_result.data:
                    continue
                
                # Analyze each odds entry for value
                for odds in odds_result.data:
                    if not odds.get("price") or not odds.get("team"):
                        continue
                    
                    # Simple value calculation (in production, use model predictions)
                    # For now, look for odds with favorable implied probability
                    price = odds["price"]
                    implied_prob = implied_probability(price, "american")
                    
                    # Placeholder: compare to simple historical win rate
                    # In production: use model predictions
                    estimated_true_prob = implied_prob + 0.05  # Placeholder: assume 5% edge
                    
                    edge = estimated_true_prob - implied_prob
                    ev_value = expected_value(estimated_true_prob, price, "american", 1.0)
                    
                    if ev_value >= min_ev and edge >= min_edge:
                        value_bets.append({
                            "game_id": game_id,
                            "game": {
                                "home_team": game["home_team"],
                                "away_team": game["away_team"],
                                "commence_time": game["commence_time"]
                            },
                            "market_type": market_type,
                            "bookmaker": odds["bookmaker_key"],
                            "team": odds["team"],
                            "selection": odds.get("outcome_name", odds["team"]),
                            "point": odds.get("point"),
                            "odds": price,
                            "implied_prob": round(implied_prob, 4),
                            "estimated_prob": round(estimated_true_prob, 4),
                            "edge": round(edge, 4),
                            "ev": round(ev_value, 4),
                            "snapshot_time": odds["snapshot_time"],
                            "quality_gate_passed": True
                        })
        
        # Sort by EV descending
        value_bets.sort(key=lambda x: x["ev"], reverse=True)
        
        return JSONResponse(
            content={
                "value_bets": value_bets,
                "count": len(value_bets),
                "filters": {
                    "min_ev": min_ev,
                    "min_edge": min_edge,
                    "market_types": market_type_list
                },
                "generated_at": datetime.utcnow().isoformat()
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error generating value board: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate value board: {str(e)}")
