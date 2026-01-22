"""
Performance metrics endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from models import PerformanceMetrics
from backend.supabase_client import create_isolated_supabase_client, get_supabase_config

router = APIRouter()


@router.get("/api/performance", response_model=PerformanceMetrics, tags=["performance"])
async def get_performance_metrics():
    """
    Get overall performance metrics for all settled picks.
    
    Returns:
        PerformanceMetrics: Comprehensive performance statistics including ROI, win rate, and Sharpe ratio
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
        
        # Get all picks
        picks_result = supabase.table("picks").select("*").execute()
        all_picks = picks_result.data
        
        # Get all pick results
        results_result = supabase.table("pick_results").select("*").execute()
        results_by_pick = {r["pick_id"]: r for r in results_result.data}
        
        # Calculate metrics
        total_picks = len(all_picks)
        settled_picks = len([p for p in all_picks if p.get("status") == "settled"])
        
        wins = 0
        losses = 0
        pushes = 0
        total_stake_units = 0.0
        total_pnl_units = 0.0
        total_odds = 0.0
        total_ev = 0.0
        pnl_list = []
        
        for pick in all_picks:
            total_stake_units += pick.get("stake_units", 0)
            total_odds += pick.get("price", 0)
            total_ev += pick.get("ev", 0)
            
            if pick.get("status") == "settled" and pick["id"] in results_by_pick:
                result = results_by_pick[pick["id"]]
                result_type = result.get("result")
                pnl = result.get("pnl_units", 0)
                
                if result_type == "win":
                    wins += 1
                elif result_type == "loss":
                    losses += 1
                elif result_type == "push":
                    pushes += 1
                
                total_pnl_units += pnl
                pnl_list.append(pnl)
        
        # Calculate derived metrics
        win_rate = wins / settled_picks if settled_picks > 0 else 0.0
        roi = (total_pnl_units / total_stake_units * 100) if total_stake_units > 0 else 0.0
        avg_odds = total_odds / total_picks if total_picks > 0 else 0.0
        avg_ev = total_ev / total_picks if total_picks > 0 else 0.0
        
        # Calculate Sharpe ratio (risk-adjusted return)
        sharpe_ratio: Optional[float] = None
        if len(pnl_list) > 1:
            import statistics
            mean_pnl = statistics.mean(pnl_list)
            std_pnl = statistics.stdev(pnl_list)
            if std_pnl > 0:
                sharpe_ratio = mean_pnl / std_pnl
        
        # Calculate max drawdown
        max_drawdown: Optional[float] = None
        if pnl_list:
            cumulative = 0
            peak = 0
            max_dd = 0
            for pnl in pnl_list:
                cumulative += pnl
                if cumulative > peak:
                    peak = cumulative
                drawdown = peak - cumulative
                if drawdown > max_dd:
                    max_dd = drawdown
            max_drawdown = max_dd
        
        return PerformanceMetrics(
            total_picks=total_picks,
            settled_picks=settled_picks,
            wins=wins,
            losses=losses,
            pushes=pushes,
            win_rate=round(win_rate, 3),
            roi=round(roi, 2),
            total_stake_units=round(total_stake_units, 2),
            total_pnl_units=round(total_pnl_units, 2),
            avg_odds=round(avg_odds, 2),
            avg_ev=round(avg_ev, 3),
            avg_clv=None,  # TODO: Calculate from CLV data
            sharpe_ratio=round(sharpe_ratio, 3) if sharpe_ratio is not None else None,
            max_drawdown=round(max_drawdown, 2) if max_drawdown is not None else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")
