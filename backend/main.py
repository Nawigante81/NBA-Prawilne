"""
NBA Betting Analytics API
A FastAPI application for NBA betting analytics and predictions.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import settings
from db import init_db_pool, close_db_pool
from services.sync_service import setup_scheduler, shutdown_scheduler
from api import (
    routes_health,
    routes_status,
    routes_team,
    routes_game,
    routes_odds,
    routes_value,
    routes_picks,
    routes_performance,
)


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger.info("Starting up NBA Betting Analytics API...")
    
    scheduler = None
    try:
        # Initialize database pool
        await init_db_pool()
        logger.info("Database pool initialized")
        
        # Setup scheduler (non-async function)
        scheduler = setup_scheduler()
        logger.info("Scheduler initialized")
        
        yield
        
    finally:
        # Shutdown
        logger.info("Shutting down NBA Betting Analytics API...")
        
        # Shutdown scheduler
        if scheduler:
            shutdown_scheduler(scheduler)
            logger.info("Scheduler shut down")
        
        # Close database pool
        await close_db_pool()
        logger.info("Database pool closed")


# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(routes_health.router)
app.include_router(routes_status.router)
app.include_router(routes_team.router)
app.include_router(routes_game.router)
app.include_router(routes_odds.router)
app.include_router(routes_value.router)
app.include_router(routes_picks.router)
app.include_router(routes_performance.router)


logger.info("NBA Betting Analytics API initialized successfully")
