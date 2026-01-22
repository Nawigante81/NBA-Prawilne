"""
Picks API routes.
Manage betting recommendations and settlements.
"""
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from typing import List
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from db import get_db
from services.value_service import get_value_service
from services.quality_gates import get_quality_gate_service
from services.clv_service import get_clv_service
from services.betting_math import expected_value, implied_probability
from settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/picks", tags=["picks"])


class SettlePickRequest(BaseModel):
    pick_id: str
    result: str
    admin_key: str


@router.get("/today")
async def get_todays_picks():
    """Return recommended picks for today/tomorrow."""
    try:
        value_service = get_value_service()
        quality_gates = get_quality_gate_service()
        db = get_db()

        picks = []
        no_bets = []
        items = []
        value_rows = value_service.get_value_board(window_days=2)

        # map team name to abbreviation for stats recency gate
        name_to_abbr = {}
        teams_result = db.table("teams").select("abbreviation,full_name").execute()
        for t in teams_result.data or []:
            name = t.get("full_name")
            abbr = t.get("abbreviation")
            if name and abbr:
                name_to_abbr[name] = abbr

        for row in value_rows:
            if row.get("skip_gates") or ("TIMEOUT" in (row.get("reasons") or [])):
                row.setdefault("decision", "NO_BET")
                row.setdefault("reasons", ["TIMEOUT"])
                row.setdefault("details", {})
                items.append(row)
                no_bets.append(row)
                continue

            reasons = []
            details = {}
            if row.get("ev") is None or row.get("edge_prob") is None:
                reasons.append("MISSING_METRICS")
            if row.get("ev") is not None and row["ev"] < settings.min_ev:
                reasons.append("EV_TOO_LOW")
            if row.get("edge_prob") is not None and row["edge_prob"] < settings.min_edge_prob:
                reasons.append("EDGE_TOO_SMALL")

            gate = await quality_gates.check_odds_availability(row.get("game_id"), row.get("market_type"))
            if not gate.passed:
                reasons.extend([r.value for r in gate.reasons])
                details.update({"odds": gate.details})

            team_abbr = name_to_abbr.get(row.get("selection"))
            if team_abbr:
                stats_gate = await quality_gates.check_stats_recency(team_abbr)
                if not stats_gate.passed:
                    reasons.extend([r.value for r in stats_gate.reasons])
                    details.update({"stats": stats_gate.details})

            row.update({
                "decision": "BET" if len(reasons) == 0 else "NO_BET",
                "reasons": reasons,
                "details": details,
            })

            items.append(row)
            if len(reasons) == 0:
                picks.append(row)
            else:
                no_bets.append(row)

        picks.sort(key=lambda x: x.get("ev") or -999, reverse=True)
        no_bets.sort(key=lambda x: x.get("ev") or -999, reverse=True)
        return JSONResponse(
            content={
                "picks": picks,
                "no_bets": no_bets,
                "items": items,
                "count": len(picks),
                "count_no_bet": len(no_bets),
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error fetching today's picks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch picks: {str(e)}")


@router.post("/settle")
async def settle_pick(request: SettlePickRequest):
    """Settle a pick (admin)."""
    try:
        if request.admin_key != settings.admin_api_key:
            raise HTTPException(status_code=403, detail="Invalid admin key")

        db = get_db()
        clv_service = get_clv_service()

        pick_result = db.table("picks").select("*").eq("id", request.pick_id).execute()
        if not pick_result.data:
            raise HTTPException(status_code=404, detail="Pick not found")

        pick = pick_result.data[0]
        closing_line = await clv_service.get_closing_line(
            game_id=pick.get("game_id"),
            market_type=pick.get("market_type"),
            team=pick.get("selection"),
        )

        closing_odds = closing_line.get("price") if closing_line else None
        closing_point = closing_line.get("point") if closing_line else None
        clv = None
        if closing_line and closing_odds is not None:
            clv = await clv_service.calculate_clv_for_pick(request.pick_id)

        # PNL is passed in result; here set 0 placeholder
        pnl_units = 0.0
        db.table("pick_results").insert({
            "pick_id": request.pick_id,
            "status": request.result,
            "closing_odds": closing_odds,
            "closing_point": closing_point,
            "clv": clv,
            "profit_loss": pnl_units,
            "settled_at": datetime.utcnow().isoformat(),
        }).execute()

        db.table("picks").update({"status": request.result}).eq("id", request.pick_id).execute()

        return JSONResponse(content={"ok": True, "pick_id": request.pick_id}, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error settling pick: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to settle pick: {str(e)}")
