"""
Pydantic models for the NBA Analytics Platform.
All providers must output these normalized models.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class OddsFormat(str, Enum):
    """Supported odds formats."""
    AMERICAN = "american"
    DECIMAL = "decimal"


class MarketType(str, Enum):
    """Supported market types."""
    H2H = "h2h"  # Moneyline
    SPREADS = "spreads"
    TOTALS = "totals"


class PickStatus(str, Enum):
    """Pick lifecycle status."""
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    PUSH = "push"
    VOID = "void"


class GateFailureReason(str, Enum):
    """Quality gate failure reasons."""
    NO_ODDS_RECENT = "NO_ODDS_RECENT"
    NO_ODDS = "NO_ODDS"
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    EV_TOO_LOW = "EV_TOO_LOW"
    HIGH_JUICE = "HIGH_JUICE"
    MISSING_COMMENCE_TIME = "MISSING_COMMENCE_TIME"
    PLAYER_MINUTES_UNKNOWN = "PLAYER_MINUTES_UNKNOWN"
    STATS_TOO_OLD = "STATS_TOO_OLD"
    STATS_STALE = "STATS_STALE"
    MISSING_CLOSING_LINE = "MISSING_CLOSING_LINE"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    EDGE_TOO_SMALL = "EDGE_TOO_SMALL"


# Base models
class Team(BaseModel):
    """NBA Team."""
    id: Optional[str] = None
    abbreviation: str
    full_name: str
    name: str
    city: Optional[str] = None
    created_at: Optional[datetime] = None


class Player(BaseModel):
    """NBA Player."""
    id: Optional[str] = None
    name: str
    player_id: Optional[int] = None  # NBA API ID
    jersey_number: Optional[int] = None
    team_id: Optional[str] = None
    team_abbreviation: str
    position: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[int] = None
    age: Optional[int] = None
    birth_date: Optional[date] = None
    experience: Optional[int] = None
    college: Optional[str] = None
    is_active: bool = True
    season_year: str = "2024-25"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Game(BaseModel):
    """NBA Game."""
    id: str
    sport_key: str = "basketball_nba"
    sport_title: str = "NBA"
    commence_time: datetime
    home_team: str
    away_team: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TeamGameStat(BaseModel):
    """Team statistics for a single game."""
    id: Optional[str] = None
    game_id: str
    team_abbreviation: str
    game_date: date
    is_home: bool
    points: Optional[int] = None
    opponent_points: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    three_point_made: Optional[int] = None
    three_point_attempted: Optional[int] = None
    free_throws_made: Optional[int] = None
    free_throws_attempted: Optional[int] = None
    offensive_rebounds: Optional[int] = None
    defensive_rebounds: Optional[int] = None
    total_rebounds: Optional[int] = None
    assists: Optional[int] = None
    steals: Optional[int] = None
    blocks: Optional[int] = None
    turnovers: Optional[int] = None
    personal_fouls: Optional[int] = None
    offensive_rating: Optional[float] = None
    defensive_rating: Optional[float] = None
    pace: Optional[float] = None
    created_at: Optional[datetime] = None


class PlayerGameStat(BaseModel):
    """Player statistics for a single game."""
    id: Optional[str] = None
    player_id: str
    game_id: str
    game_date: date
    team_abbreviation: str
    opponent_abbreviation: str
    minutes: Optional[float] = None
    points: Optional[int] = None
    rebounds: Optional[int] = None
    assists: Optional[int] = None
    steals: Optional[int] = None
    blocks: Optional[int] = None
    turnovers: Optional[int] = None
    field_goals_made: Optional[int] = None
    field_goals_attempted: Optional[int] = None
    three_point_made: Optional[int] = None
    three_point_attempted: Optional[int] = None
    free_throws_made: Optional[int] = None
    free_throws_attempted: Optional[int] = None
    plus_minus: Optional[int] = None
    created_at: Optional[datetime] = None


class OddsSnapshot(BaseModel):
    """Odds snapshot at a point in time."""
    id: Optional[str] = None
    game_id: str
    bookmaker_key: str
    bookmaker_title: Optional[str] = None
    market_type: str
    outcome_name: Optional[str] = None
    team: Optional[str] = None
    point: Optional[float] = None
    price: Optional[float] = None  # American or Decimal
    ts: datetime
    content_hash: Optional[str] = None  # For deduplication
    created_at: Optional[datetime] = None


class ClosingLine(BaseModel):
    """Consensus closing line for a game/market."""
    id: Optional[str] = None
    game_id: str
    market_type: str
    team: Optional[str] = None
    point: Optional[float] = None
    price: Optional[float] = None
    ts_cutoff: datetime
    method: str
    sample_count: int
    used_bookmakers: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class Pick(BaseModel):
    """A betting recommendation."""
    id: Optional[str] = None
    game_id: str
    market_type: str
    selection: str  # Team name or outcome
    bookmaker: str
    odds: float  # Price at time of pick
    odds_format: OddsFormat = OddsFormat.AMERICAN
    point: Optional[float] = None  # For spreads/totals
    stake_units: float
    stake_usd: float
    edge: float  # Expected edge (model_prob - implied_prob)
    ev: float  # Expected value
    confidence: float  # Model confidence
    kelly_fraction: float
    notes: Optional[str] = None
    pick_time: datetime
    game_commence_time: datetime
    status: PickStatus = PickStatus.PENDING
    created_at: Optional[datetime] = None


class PickResult(BaseModel):
    """Result of a settled pick."""
    id: Optional[str] = None
    pick_id: str
    status: PickStatus
    closing_odds: Optional[float] = None
    closing_point: Optional[float] = None
    clv: Optional[float] = None  # Closing Line Value
    profit_loss: float
    settled_at: datetime
    created_at: Optional[datetime] = None


class Report(BaseModel):
    """Generated report."""
    id: Optional[str] = None
    report_type: str  # "750am", "800am", "1100am"
    report_date: date
    content: Dict[str, Any]
    generated_at: datetime
    created_at: Optional[datetime] = None


class APIBudgetEntry(BaseModel):
    """Daily API call budget tracking."""
    id: Optional[str] = None
    provider: str  # "odds_api", "nba_api", "basketball_reference"
    date: date
    calls_made: int = 0
    calls_limit: int
    last_call_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class APICacheEntry(BaseModel):
    """Cached API response."""
    id: Optional[str] = None
    provider: str
    endpoint: str
    params_hash: str
    response_data: Dict[str, Any]
    ttl_seconds: int
    cached_at: datetime
    expires_at: datetime
    created_at: Optional[datetime] = None


class UploadStub(BaseModel):
    """Metadata for uploaded bookmaker screenshots."""
    id: Optional[str] = None
    filename: str
    upload_date: datetime
    bookmaker: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class QualityGateResult(BaseModel):
    """Result of quality gate checks."""
    passed: bool
    reasons: List[GateFailureReason] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
