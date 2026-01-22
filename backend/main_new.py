"""
NBA Analytics Platform - Main Application Entry Point.

This module provides a clean FastAPI application with:
- Scheduled data synchronization and report generation
- RESTful API for analytics queries
- Basic authentication and CORS
- Comprehensive error handling and logging
"""
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import our API routers
from api import (
    teams_router,
    games_router,
    odds_router,
    value_board_router,
    picks_router,
    performance_router,
    reports_router,
    uploads_router,
)

# Import our services
from services.sync_service import get_sync_service
from services.report_service import get_report_service
from services.budget_service import get_budget_service
from settings import settings

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/main.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    global scheduler
    
    logger.info("=" * 80)
    logger.info("NBA Analytics Platform - Starting Up")
    logger.info("=" * 80)
    
    # Initialize services
    sync_service = get_sync_service()
    report_service = get_report_service()
    budget_service = get_budget_service()
    
    # Initialize scheduler
    scheduler = AsyncIOScheduler(timezone=settings.timezone)
    
    # Schedule startup sync (runs immediately)
    logger.info("Scheduling startup sync...")
    try:
        await sync_service.startup_sync()
        logger.info("✓ Startup sync completed successfully")
    except Exception as e:
        logger.error(f"✗ Startup sync failed: {e}", exc_info=True)
    
    # Schedule periodic data sync every 12 hours
    scheduler.add_job(
        sync_service.scheduled_sync,
        trigger='interval',
        hours=12,
        id='periodic_sync',
        name='Periodic Data Sync (every 12 hours)',
        replace_existing=True
    )
    logger.info("✓ Scheduled periodic sync (every 12 hours)")
    
    # Schedule daily reports at specific times (Chicago timezone)
    # 7:50 AM Report
    scheduler.add_job(
        lambda: report_service.generate_750am_report(),
        trigger=CronTrigger(hour=7, minute=50, timezone=settings.timezone),
        id='report_0750',
        name='Daily Report 7:50 AM',
        replace_existing=True
    )
    logger.info("✓ Scheduled daily report at 7:50 AM (America/Chicago)")
    
    # 8:00 AM Report
    scheduler.add_job(
        lambda: report_service.generate_800am_report(),
        trigger=CronTrigger(hour=8, minute=0, timezone=settings.timezone),
        id='report_0800',
        name='Daily Report 8:00 AM',
        replace_existing=True
    )
    logger.info("✓ Scheduled daily report at 8:00 AM (America/Chicago)")
    
    # 11:00 AM Report
    scheduler.add_job(
        lambda: report_service.generate_1100am_report(),
        trigger=CronTrigger(hour=11, minute=0, timezone=settings.timezone),
        id='report_1100',
        name='Daily Report 11:00 AM',
        replace_existing=True
    )
    logger.info("✓ Scheduled daily report at 11:00 AM (America/Chicago)")
    
    # Start the scheduler
    scheduler.start()
    logger.info("✓ APScheduler started")
    logger.info("=" * 80)
    logger.info("Application ready to accept requests")
    logger.info("=" * 80)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("✓ APScheduler stopped")
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="NBA Analytics Platform API",
    description="RESTful API for NBA betting analytics with data synchronization and reporting",
    version="2.0.0",
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic Authentication Middleware
@app.middleware("http")
async def basic_auth_middleware(request: Request, call_next):
    """
    Basic authentication middleware.
    Exempts /health, /docs, /openapi.json, and /redoc endpoints.
    """
    # Exempt paths
    exempt_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    if any(request.url.path.startswith(path) for path in exempt_paths):
        return await call_next(request)
    
    # Check Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.replace("Bearer ", "")
    if token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return await call_next(request)


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )


# Core Endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    Returns basic application health status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "NBA Analytics Platform",
        "version": "2.0.0"
    }


@app.get("/api/status")
async def system_status() -> Dict[str, Any]:
    """
    System status endpoint with provider health checks.
    Returns detailed status of all system components.
    """
    try:
        # Check scheduler status
        scheduler_status = "running" if scheduler and scheduler.running else "stopped"
        scheduled_jobs = []
        if scheduler:
            for job in scheduler.get_jobs():
                scheduled_jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
        
        # Check provider health (skipped for now - would require DB connection)
        providers_health = {
            "nba_stats": {"status": "not_checked"},
            "the_odds_api": {"status": "not_checked"},
        }
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "scheduler": {
                "status": scheduler_status,
                "jobs": scheduled_jobs
            },
            "providers": providers_health,
            "settings": {
                "timezone": settings.timezone,
                "odds_fetch_interval_hours": settings.odds_fetch_interval_hours,
                "max_calls_per_day": settings.odds_max_calls_per_day,
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system status: {str(e)}"
        )


@app.get("/api/budget")
async def api_budget() -> Dict[str, Any]:
    """
    API budget usage endpoint.
    Returns today's API call budget usage.
    """
    try:
        budget_service = get_budget_service()
        budget_data = await budget_service.get_budget_summary()
        return budget_data
    except Exception as e:
        logger.error(f"Error getting budget usage: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get budget usage: {str(e)}"
        )


# Mount API Routers
app.include_router(teams_router, prefix="/api", tags=["Teams"])
app.include_router(games_router, prefix="/api", tags=["Games"])
app.include_router(odds_router, prefix="/api", tags=["Odds"])
app.include_router(value_board_router, prefix="/api", tags=["Value Board"])
app.include_router(picks_router, prefix="/api", tags=["Picks"])
app.include_router(performance_router, prefix="/api", tags=["Performance"])
app.include_router(reports_router, prefix="/api", tags=["Reports"])
app.include_router(uploads_router, prefix="/api", tags=["Uploads"])


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "service": "NBA Analytics Platform API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "/api/status"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
