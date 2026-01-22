"""
Value board endpoint
"""
from fastapi import APIRouter, HTTPException
from datetime import date

from models import ValueBoard
from services.value_service import get_value_board_today
from services.gating_service import apply_gates_to_value_board

router = APIRouter()


@router.get("/api/value-board/today", response_model=ValueBoard, tags=["value"])
async def get_today_value_board():
    """
    Get value betting opportunities for today's games.
    Applies all gating rules to filter high-quality opportunities.
    
    Returns:
        ValueBoard: Filtered value betting opportunities with metadata
    """
    try:
        # Get raw value board for today
        raw_board = await get_value_board_today()
        
        if not raw_board:
            # Return empty board if no games today
            return ValueBoard(
                date=date.today().isoformat(),
                opportunities=[],
                total_count=0,
                filters_applied={
                    "min_edge": 0.02,
                    "min_confidence": 0.6,
                    "gating_enabled": True
                }
            )
        
        # Apply gating rules to filter opportunities
        filtered_board = apply_gates_to_value_board(raw_board)
        
        return filtered_board
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get value board: {str(e)}")
