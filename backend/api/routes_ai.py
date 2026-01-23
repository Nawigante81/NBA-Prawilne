"""
AI recommendation API routes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from services.ai_recommendation_service import get_ai_recommendation_service
from services.llm_insight_service import generate_llm_insight

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/team/{team_abbrev}/recommendation")
async def get_team_ai_recommendation(team_abbrev: str):
    """Get AI recommendation package for team's next game."""
    try:
        service = get_ai_recommendation_service()
        result = await service.get_team_recommendation(team_abbrev)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error generating AI recommendation for {team_abbrev}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate AI recommendation")


@router.get("/team/{team_abbrev}/insight")
async def get_team_ai_insight(team_abbrev: str, provider: str = "auto"):
    """Get LLM insight summary for team's next game."""
    try:
        result = await generate_llm_insight(team_abbrev, provider=provider)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        logger.error(f"Error generating LLM insight for {team_abbrev}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate AI insight")
