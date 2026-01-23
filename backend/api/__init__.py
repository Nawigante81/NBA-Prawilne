"""
API Routes Module.
Exports all routers for the NBA Analytics Platform API.
"""
from .routes_teams import router as teams_router
from .routes_games import router as games_router
from .routes_odds import router as odds_router
from .routes_value_board import router as value_board_router
from .routes_ai import router as ai_router
from .routes_picks import router as picks_router
from .routes_performance import router as performance_router
from .routes_reports import router as reports_router
from .routes_uploads_stub import router as uploads_router

__all__ = [
    "teams_router",
    "games_router",
    "odds_router",
    "value_board_router",
    "ai_router",
    "picks_router",
    "performance_router",
    "reports_router",
    "uploads_router",
]
