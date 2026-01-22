"""
Health check endpoint
"""
from fastapi import APIRouter
from datetime import datetime

from models import HealthCheck

router = APIRouter()


@router.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        HealthCheck: Simple health status with timestamp
    """
    return HealthCheck(
        status="ok",
        timestamp=datetime.utcnow()
    )
