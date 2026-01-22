"""
Value Board API routes.
Shows betting opportunities that pass quality gates.
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from datetime import datetime
import logging

from db import get_db
from services.value_service import get_value_service
from services.quality_gates import get_quality_gate_service
from settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/value-board", tags=["value-board"])


@router.get("/today")
async def get_value_board_today(
    min_ev: float = Query(0.02, description="Minimum expected value", ge=0.0),
    min_edge: float = Query(0.03, description="Minimum edge", ge=0.0),
):
    """Get value bets for today/tomorrow with quality gates."""
    try:
        db = get_db()
        value_service = get_value_service()
        quality_gates = get_quality_gate_service()

        value_rows = value_service.get_value_board(window_days=2)
        if not value_rows:
            return JSONResponse(content={"value_bets": [], "count": 0}, status_code=200)

        name_to_abbr = {}
        teams_result = db.table("teams").select("abbreviation,full_name").execute()
        for t in teams_result.data or []:
            name = t.get("full_name")
            abbr = t.get("abbreviation")
            if name and abbr:
                name_to_abbr[name] = abbr

        value_bets = []
        for row in value_rows:
            reasons = []
            details = {}

            game_id = row.get("game_id")
            market_type = row.get("market_type")
            selection = row.get("selection")

            odds_gate = await quality_gates.check_odds_availability(game_id, market_type)
            if not odds_gate.passed:
                reasons.extend([r.value for r in odds_gate.reasons])
                details.update({"odds": odds_gate.details})

            team_abbr = name_to_abbr.get(selection) if selection else None
            if team_abbr:
                stats_gate = await quality_gates.check_stats_recency(team_abbr)
                if not stats_gate.passed:
                    reasons.extend([r.value for r in stats_gate.reasons])
                    details.update({"stats": stats_gate.details})

            if row.get("ev") is not None and row.get("ev") < min_ev:
                reasons.append("EV_TOO_LOW")
            if row.get("edge_prob") is not None and row.get("edge_prob") < min_edge:
                reasons.append("EDGE_TOO_SMALL")

            row.update({
                "quality_gate_passed": len(reasons) == 0,
                "reasons": reasons,
                "details": details,
            })

            if len(reasons) == 0:
                value_bets.append(row)

        value_bets.sort(key=lambda x: x.get("ev") or -999, reverse=True)

        return JSONResponse(
            content={
                "value_bets": value_bets,
                "count": len(value_bets),
                "filters": {"min_ev": min_ev, "min_edge": min_edge},
                "generated_at": datetime.utcnow().isoformat(),
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error generating value board: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate value board: {str(e)}")
