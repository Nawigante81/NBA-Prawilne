"""
Performance API routes.
Track ROI, CLV, and betting performance metrics.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, date, timedelta
import logging

from db import get_db
from services.clv_service import CLVService
from models import PickStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/performance", tags=["performance"])


@router.get("")
async def get_performance_summary(
    days_back: int = Query(30, description="Days of history to analyze", ge=1, le=365),
    market_type: Optional[str] = Query(None, description="Filter by market type")
):
    """
    Get ROI and CLV performance summary.
    
    Calculates:
    - Overall ROI
    - Average CLV
    - Win rate
    - Total P&L
    - Picks breakdown by status
    
    Args:
        days_back: Number of days to analyze
        market_type: Optional market type filter
    
    Returns:
        Performance metrics and summary statistics
    """
    try:
        db = get_db()
        clv_service = CLVService()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # Get picks in date range
        query = db.table("picks").select("*").gte(
            "pick_time", start_date.isoformat()
        ).lte(
            "pick_time", end_date.isoformat()
        )
        
        if market_type:
            query = query.eq("market_type", market_type)
        
        picks_result = query.execute()
        
        if not picks_result.data:
            return JSONResponse(
                content={
                    "message": "No picks found in date range",
                    "days_back": days_back,
                    "market_type": market_type
                },
                status_code=200
            )
        
        picks = picks_result.data
        
        # Get corresponding pick results
        pick_ids = [p["id"] for p in picks]
        results_query = db.table("pick_results").select("*").in_("pick_id", pick_ids).execute()
        results = results_query.data if results_query.data else []
        
        # Calculate metrics
        total_picks = len(picks)
        total_stake = sum(p.get("stake_usd", 0) for p in picks)
        
        # Status breakdown
        status_counts = {}
        for status in PickStatus:
            count = sum(1 for p in picks if p.get("status") == status.value)
            status_counts[status.value] = count
        
        # Calculate P&L and ROI
        total_profit = sum(r.get("profit_loss", 0) for r in results)
        roi = (total_profit / total_stake * 100) if total_stake > 0 else 0

        # Drawdown from cumulative P&L
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for r in sorted(results, key=lambda x: x.get("settled_at") or ""):
            cumulative += float(r.get("profit_loss") or 0)
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Calculate win rate (won / (won + lost))
        won_count = status_counts.get(PickStatus.WON.value, 0)
        lost_count = status_counts.get(PickStatus.LOST.value, 0)
        decided_count = won_count + lost_count
        win_rate = (won_count / decided_count * 100) if decided_count > 0 else 0
        
        # Calculate average CLV
        clv_values = [r.get("clv", 0) for r in results if r.get("clv") is not None]
        avg_clv = sum(clv_values) / len(clv_values) if clv_values else 0
        
        # Calculate average edge and EV
        avg_edge = sum(p.get("edge", 0) for p in picks) / total_picks if total_picks > 0 else 0
        avg_ev = sum(p.get("ev", 0) for p in picks) / total_picks if total_picks > 0 else 0
        
        # Market breakdown
        market_breakdown = {}
        if not market_type:
            for mkt in ["h2h", "spreads", "totals"]:
                mkt_picks = [p for p in picks if p.get("market_type") == mkt]
                if mkt_picks:
                    mkt_results = [r for r in results if any(p["id"] == r["pick_id"] for p in mkt_picks)]
                    mkt_profit = sum(r.get("profit_loss", 0) for r in mkt_results)
                    mkt_stake = sum(p.get("stake_usd", 0) for p in mkt_picks)
                    mkt_roi = (mkt_profit / mkt_stake * 100) if mkt_stake > 0 else 0
                    
                    market_breakdown[mkt] = {
                        "picks": len(mkt_picks),
                        "profit": round(mkt_profit, 2),
                        "roi": round(mkt_roi, 2)
                    }
        
        return JSONResponse(
            content={
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days_back
                },
                "summary": {
                    "total_picks": total_picks,
                    "total_stake_usd": round(total_stake, 2),
                    "total_profit_usd": round(total_profit, 2),
                    "roi_percent": round(roi, 2),
                    "yield_percent": round(roi, 2),
                    "win_rate_percent": round(win_rate, 2),
                    "average_clv": round(avg_clv, 4),
                    "average_edge": round(avg_edge, 4),
                    "average_ev": round(avg_ev, 4),
                    "max_drawdown": round(max_drawdown, 2)
                },
                "status_breakdown": status_counts,
                "market_breakdown": market_breakdown if market_breakdown else None
            },
            status_code=200
        )
    
    except Exception as e:
        logger.error(f"Error calculating performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate performance: {str(e)}")
