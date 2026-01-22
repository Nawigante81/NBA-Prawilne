"""
NBA Betting Analytics Backend - Pydantic Models
Data models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================================================================
# ENUMS
# ==================================================================

class MarketType(str, Enum):
    H2H = "h2h"
    SPREAD = "spread"
    TOTALS = "totals"


class PickStatus(str, Enum):
    OPEN = "open"
    SETTLED = "settled"
    VOID = "void"


class PickResult(str, Enum):
    WIN = "win"
    LOSS = "loss"
    PUSH = "push"
    VOID = "void"


class GameStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINAL = "final"
    POSTPONED = "postponed"


class PlayerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    UNKNOWN = "UNKNOWN"
    DNP_FLAG = "DNP_FLAG"


# ==================================================================
# TEAM MODELS
# ==================================================================

class TeamBettingStats(BaseModel):
    """Team betting statistics response"""
    team_abbrev: str
    window: int = Field(default=20, description="Number of games in window")
    
    # ATS Stats
    ats_record: str = Field(description="ATS record (W-L-P)")
    ats_win_pct: float
    ats_roi: float
    avg_spread_diff: float = Field(description="Average spread differential")
    
    # O/U Stats
    ou_record: str = Field(description="O/U record (O-U-P)")
    over_pct: float
    avg_total_diff: float = Field(description="Average total differential")
    avg_total_points: float
    
    # Additional metrics
    games_analyzed: int
    last_updated: datetime


class TeamNextGame(BaseModel):
    """Next game for a team"""
    game_id: str
    opponent: str
    is_home: bool
    commence_time: datetime
    odds_available: bool


class KeyPlayer(BaseModel):
    """Key player information"""
    player_id: str
    name: str
    position: Optional[str]
    avg_minutes: float = Field(description="Average minutes last 5 games")
    minutes_trend: str = Field(description="UP, DOWN, or STABLE")
    status: PlayerStatus
    games_played: int


# ==================================================================
# GAME MODELS
# ==================================================================

class Game(BaseModel):
    """Game information"""
    id: str
    home_team: str
    away_team: str
    commence_time: datetime
    status: GameStatus
    nba_game_id: Optional[str]


class GameOdds(BaseModel):
    """Current odds for a game"""
    game_id: str
    market_type: MarketType
    bookmaker_key: str
    team: Optional[str]
    outcome_name: Optional[str]
    point: Optional[float]
    price: float
    timestamp: datetime


class ConsensusLine(BaseModel):
    """Consensus line from multiple bookmakers"""
    game_id: str
    market_type: MarketType
    team: Optional[str]
    point: Optional[float]
    price: float
    method: str = "consensus_median_mad"
    sample_count: int
    used_bookmakers: List[str]
    outliers_removed: int = 0
    timestamp: datetime


class OddsMovement(BaseModel):
    """Odds movement over time"""
    game_id: str
    market_type: MarketType
    team: Optional[str]
    snapshots: List[Dict[str, Any]] = Field(description="Historical odds snapshots")
    current_line: Optional[float]
    opening_line: Optional[float]
    movement: Optional[float] = Field(description="Line movement (current - opening)")


class CLVData(BaseModel):
    """Closing Line Value data"""
    game_id: str
    market_type: MarketType
    team: Optional[str]
    closing_line: float
    closing_price: float
    opening_line: Optional[float]
    opening_price: Optional[float]
    clv_points: Optional[float] = Field(description="Points of CLV")
    method: str
    sample_count: int


# ==================================================================
# VALUE MODELS
# ==================================================================

class ValueBet(BaseModel):
    """Value bet opportunity"""
    game_id: str
    market: MarketType
    team_abbrev: Optional[str]
    selection: str
    line: Optional[float]
    price: float
    implied_prob: float
    model_prob: float
    edge_prob: float
    ev: float
    kelly_fraction: float
    stake_units: float
    confidence: float
    reason_codes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValueBoard(BaseModel):
    """Value board response"""
    date: str
    opportunities: List[ValueBet]
    total_count: int
    filters_applied: Dict[str, Any]


# ==================================================================
# PICK MODELS
# ==================================================================

class Pick(BaseModel):
    """Pick/bet record"""
    id: str
    created_at: datetime
    game_id: Optional[str]
    team_abbrev: Optional[str]
    market: MarketType
    selection: str
    line: Optional[float]
    price: float
    implied_prob: float
    model_prob: float
    edge_prob: float
    ev: float
    kelly_fraction: float
    stake_units: float
    reason_codes: List[str]
    status: PickStatus


class PickResult(BaseModel):
    """Pick result record"""
    pick_id: str
    settled_at: datetime
    result: PickResult
    pnl_units: float


class SettlePickRequest(BaseModel):
    """Request to settle a pick"""
    pick_id: str
    result: PickResult
    pnl_units: float


# ==================================================================
# PERFORMANCE MODELS
# ==================================================================

class PerformanceMetrics(BaseModel):
    """Overall performance metrics"""
    total_picks: int
    settled_picks: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    roi: float
    total_stake_units: float
    total_pnl_units: float
    avg_odds: float
    avg_ev: float
    avg_clv: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]


class PerformanceByMarket(BaseModel):
    """Performance breakdown by market type"""
    market: MarketType
    picks: int
    wins: int
    losses: int
    win_rate: float
    roi: float
    total_pnl_units: float


# ==================================================================
# STATUS MODELS
# ==================================================================

class SystemStatus(BaseModel):
    """System status response"""
    status: str = Field(default="healthy")
    timestamp: datetime
    database: bool
    odds_api_budget: Dict[str, Any]
    last_sync_nba_stats: Optional[datetime]
    last_sync_odds: Optional[datetime]
    cached_games_count: int


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(default="ok")
    timestamp: datetime
