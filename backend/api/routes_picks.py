"""
Picks management endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import date, datetime
from typing import List

from models import Pick, SettlePickRequest, PickStatus
from backend.supabase_client import create_isolated_supabase_client, get_supabase_config

router = APIRouter()


@router.get("/api/picks/today", response_model=List[Pick], tags=["picks"])
async def get_todays_picks():
    """
    Get all picks made for today's games.
    
    Returns:
        List[Pick]: List of picks for today
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
        
        # Query picks for today
        result = supabase.table("picks").select("*").gte(
            "created_at", start_of_day
        ).lte(
            "created_at", end_of_day
        ).order("created_at", desc=True).execute()
        
        picks = []
        for pick_data in result.data:
            picks.append(Pick(
                id=pick_data["id"],
                created_at=datetime.fromisoformat(pick_data["created_at"]),
                game_id=pick_data.get("game_id"),
                team_abbrev=pick_data.get("team_abbrev"),
                market=pick_data["market"],
                selection=pick_data["selection"],
                line=pick_data.get("line"),
                price=pick_data["price"],
                implied_prob=pick_data["implied_prob"],
                model_prob=pick_data["model_prob"],
                edge_prob=pick_data["edge_prob"],
                ev=pick_data["ev"],
                kelly_fraction=pick_data["kelly_fraction"],
                stake_units=pick_data["stake_units"],
                reason_codes=pick_data.get("reason_codes", []),
                status=PickStatus(pick_data.get("status", "open"))
            ))
        
        return picks
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get today's picks: {str(e)}")


@router.post("/api/picks/settle", tags=["picks"])
async def settle_pick(request: SettlePickRequest):
    """
    Settle a pick by recording its result and P&L.
    
    Args:
        request: SettlePickRequest with pick_id, result, and pnl_units
    
    Returns:
        dict: Success message with pick_id
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
        
        # Verify pick exists
        pick_result = supabase.table("picks").select("*").eq("id", request.pick_id).execute()
        
        if not pick_result.data:
            raise HTTPException(status_code=404, detail=f"Pick '{request.pick_id}' not found")
        
        pick = pick_result.data[0]
        
        if pick.get("status") == "settled":
            raise HTTPException(status_code=400, detail=f"Pick '{request.pick_id}' is already settled")
        
        # Update pick status
        supabase.table("picks").update({
            "status": "settled"
        }).eq("id", request.pick_id).execute()
        
        # Insert pick result
        supabase.table("pick_results").insert({
            "pick_id": request.pick_id,
            "settled_at": datetime.utcnow().isoformat(),
            "result": request.result.value,
            "pnl_units": request.pnl_units
        }).execute()
        
        return {
            "success": True,
            "pick_id": request.pick_id,
            "result": request.result.value,
            "pnl_units": request.pnl_units
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to settle pick: {str(e)}")
