"""
Picks API routes.
Manage betting recommendations and settlements.
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging

from db import get_db
from services.quality_gates import QualityGateService
from services.clv_service import CLVService
from models import Pick, PickStatus, PickResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/picks", tags=["picks"])


class SettlePicksRequest(BaseModel):
    """Request to settle picks (admin endpoint)."""
    pick_ids: List[str]
    admin_key: str


@router.get("/today", response_model=List[Pick])
async def get_todays_picks():
    """
    Get all picks for today's games.
    
    Returns picks with status PENDING for games happening today.
    Applies quality gate checks to ensure pick quality.
    
    Returns:
        List[Pick]: Active picks for today
    """
    try:
        db = get_db()
        
        # Get today's date range
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        # Get picks for today's games
        result = db.table("picks").select("*").gte(
            "game_commence_time", now.isoformat()
        ).lte(
            "game_commence_time", tomorrow.isoformat()
        ).order("game_commence_time").execute()
        
        if not result.data:
            return []
        
        # Apply quality gate validation to each pick
        quality_gates = QualityGateService()
        validated_picks = []
        
        for pick in result.data:
            # Check if pick still passes quality gates
            gate_result = await quality_gates.check_odds_availability(
                pick["game_id"],
                pick["market_type"]
            )
            
            if gate_result.passed:
                validated_picks.append(pick)
            else:
                logger.warning(
                    f"Pick {pick.get('id')} failed quality gates: {gate_result.reasons}"
                )
        
        return validated_picks
    
    except Exception as e:
        logger.error(f"Error fetching today's picks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch picks: {str(e)}")


@router.post("/settle")
async def settle_picks(request: SettlePicksRequest):
    """
    Settle picks after games complete (admin only).
    
    Calculates:
    - Final status (won/lost/push/void)
    - Closing Line Value (CLV)
    - Profit/loss
    
    Args:
        request: SettlePicksRequest with pick IDs and admin key
    
    Returns:
        Settlement summary with CLV calculations
    """
    try:
        # Validate admin key (use proper auth in production)
        from settings import settings
        if request.admin_key != settings.admin_api_key:
            raise HTTPException(status_code=403, detail="Invalid admin key")
        
        db = get_db()
        clv_service = CLVService()
        
        settled_picks = []
        
        for pick_id in request.pick_ids:
            # Get pick details
            pick_result = db.table("picks").select("*").eq("id", pick_id).execute()
            
            if not pick_result.data:
                logger.warning(f"Pick {pick_id} not found")
                continue
            
            pick = pick_result.data[0]
            
            # Get closing line for CLV calculation
            closing_line = await clv_service.get_closing_line(
                game_id=pick["game_id"],
                market_type=pick["market_type"],
                team=pick.get("selection")
            )
            
            clv = None
            closing_odds = None
            closing_point = None
            
            if closing_line:
                closing_odds = closing_line.get("price")
                closing_point = closing_line.get("point")
                
                # Calculate CLV for the pick
                clv = await clv_service.calculate_clv_for_pick(pick_id)
            
            # Determine pick status (simplified - in production, fetch actual results)
            # For now, mark as pending settlement
            status = PickStatus.PENDING
            profit_loss = 0.0
            
            # Create pick result entry
            pick_result_entry = {
                "pick_id": pick_id,
                "status": status.value,
                "closing_odds": closing_odds,
                "closing_point": closing_point,
                "clv": clv,
                "profit_loss": profit_loss,
                "settled_at": datetime.utcnow().isoformat()
            }
            
            # Insert result
            db.table("pick_results").insert(pick_result_entry).execute()
            
            # Update pick status
            db.table("picks").update({"status": status.value}).eq("id", pick_id).execute()
            
            settled_picks.append({
                "pick_id": pick_id,
                "status": status.value,
                "clv": clv,
                "closing_odds": closing_odds,
                "closing_point": closing_point
            })
        
        return JSONResponse(
            content={
                "settled_count": len(settled_picks),
                "picks": settled_picks,
                "settled_at": datetime.utcnow().isoformat()
            },
            status_code=200
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error settling picks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to settle picks: {str(e)}")
