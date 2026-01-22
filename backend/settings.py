"""
Settings and configuration management for NBA Analytics Platform.
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from backend/.env explicitly
_env_backend = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(_env_backend, override=False)


class Settings(BaseSettings):
    """Application settings."""
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "") or os.getenv("VITE_SUPABASE_URL", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # The Odds API
    odds_api_key: str = os.getenv("ODDS_API_KEY", "")
    odds_max_calls_per_day: int = int(os.getenv("ODDS_MAX_CALLS_PER_DAY", "10"))
    odds_bookmakers_allowlist: List[str] = os.getenv(
        "ODDS_BOOKMAKERS_ALLOWLIST", 
        "draftkings,betmgm,fanduel"
    ).split(",")
    odds_fetch_interval_hours: int = int(os.getenv("ODDS_FETCH_INTERVAL_HOURS", "12"))
    odds_game_window_days: int = int(os.getenv("ODDS_GAME_WINDOW_DAYS", "2"))
    odds_snapshot_dedupe_hours: int = int(os.getenv("ODDS_SNAPSHOT_DEDUPE_HOURS", "6"))
    
    # Timezone
    timezone: str = os.getenv("TIMEZONE", "America/Chicago")
    
    # Betting parameters
    bankroll_usd: float = float(os.getenv("BANKROLL_USD", "1000"))
    max_stake_pct: float = float(os.getenv("MAX_STAKE_PCT", "0.03"))
    
    # Quality gates
    min_ev: float = float(os.getenv("MIN_EV", "0.02"))
    min_edge_prob: float = float(os.getenv("MIN_EDGE_PROB", "0.03"))
    min_confidence: float = float(os.getenv("MIN_CONFIDENCE", "0.55"))
    odds_max_american_favorite: int = int(os.getenv("ODDS_MAX_AMERICAN_FAVORITE", "-160"))
    odds_max_snapshot_age_hours: int = int(os.getenv("ODDS_MAX_SNAPSHOT_AGE_HOURS", "12"))
    stats_max_age_hours: int = int(os.getenv("STATS_MAX_AGE_HOURS", "24"))
    min_games_recent: int = int(os.getenv("MIN_GAMES_RECENT", "5"))
    min_player_games_recent: int = int(os.getenv("MIN_PLAYER_GAMES_RECENT", "3"))
    parlay_max_legs: int = int(os.getenv("PARLAY_MAX_LEGS", "5"))
    parlay_min_combined_implied_prob: float = float(os.getenv("PARLAY_MIN_COMBINED_IMPLIED_PROB", "0.20"))

    # Value board performance controls
    value_board_cache_seconds: int = int(os.getenv("VALUE_BOARD_CACHE_SECONDS", "30"))
    value_board_timeout_seconds: int = int(os.getenv("VALUE_BOARD_TIMEOUT_SECONDS", "6"))
    value_board_max_games: int = int(os.getenv("VALUE_BOARD_MAX_GAMES", "12"))
    
    # Admin
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "change-me-in-production")
    
    # Rate limiting
    nba_api_scoreboard_ttl_hours: int = 1
    nba_api_players_ttl_days: int = 7
    nba_api_gamelogs_ttl_hours: int = 6
    nba_api_max_concurrent: int = 2
    
    basketball_ref_request_interval_seconds: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra environment variables


# Global settings instance
settings = Settings()
