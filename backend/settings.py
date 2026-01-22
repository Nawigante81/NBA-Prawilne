"""
NBA Betting Analytics Backend - Settings
Environment configuration and constants
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==================================================================
# SUPABASE CONFIGURATION
# ==================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("VITE_SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing required Supabase configuration")

# ==================================================================
# API KEYS
# ==================================================================
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
if not ODDS_API_KEY:
    raise ValueError("Missing ODDS_API_KEY")

# ==================================================================
# ODDS API CONFIGURATION (Budget Management)
# ==================================================================
ODDS_MAX_CALLS_PER_DAY = int(os.getenv("ODDS_MAX_CALLS_PER_DAY", "10"))
ODDS_BOOKMAKERS_ALLOWLIST = os.getenv("ODDS_BOOKMAKERS_ALLOWLIST", "draftkings,fanduel,betmgm").split(",")[:3]
ODDS_SPORT_KEY = os.getenv("ODDS_SPORT_KEY", "basketball_nba")
ODDS_REGIONS = os.getenv("ODDS_REGIONS", "us")
ODDS_MARKETS = "h2h,spreads,totals"
ODDS_SNAPSHOT_CHANGE_THRESHOLD = float(os.getenv("ODDS_SNAPSHOT_CHANGE_THRESHOLD", "0.5"))  # Minimum point/price change
ODDS_SNAPSHOT_MAX_HOURS = int(os.getenv("ODDS_SNAPSHOT_MAX_HOURS", "6"))  # Maximum hours between snapshots

# ==================================================================
# QUALITY GATES THRESHOLDS
# ==================================================================
MIN_EV = float(os.getenv("MIN_EV", "0.02"))
MIN_EDGE_PROB = float(os.getenv("MIN_EDGE_PROB", "0.03"))
ODDS_STALE_HOURS = int(os.getenv("ODDS_STALE_HOURS", "12"))
STATS_MAX_AGE_HOURS = int(os.getenv("STATS_MAX_AGE_HOURS", "24"))
MIN_GAMES_RECENT = int(os.getenv("MIN_GAMES_RECENT", "5"))
MIN_PLAYER_GAMES_RECENT = int(os.getenv("MIN_PLAYER_GAMES_RECENT", "3"))
MIN_LIQUIDITY_SAMPLES = int(os.getenv("MIN_LIQUIDITY_SAMPLES", "2"))

# ==================================================================
# NBA API CONFIGURATION
# ==================================================================
NBA_API_CACHE_TTL_SECONDS = int(os.getenv("NBA_API_CACHE_TTL_SECONDS", "3600"))  # 1 hour
NBA_STATS_WINDOW = int(os.getenv("NBA_STATS_WINDOW", "10"))  # Last N games for stats

# ==================================================================
# BETTING MODEL CONFIGURATION
# ==================================================================
HOME_COURT_ADVANTAGE = float(os.getenv("HOME_COURT_ADVANTAGE", "3.0"))  # Points
KELLY_FRACTION = float(os.getenv("KELLY_FRACTION", "0.5"))  # Half Kelly
MAX_KELLY_STAKE = float(os.getenv("MAX_KELLY_STAKE", "0.05"))  # 5% of bankroll

# ==================================================================
# CONSENSUS LINE CONFIGURATION
# ==================================================================
CONSENSUS_OUTLIER_MAD_MULTIPLIER = float(os.getenv("CONSENSUS_OUTLIER_MAD_MULTIPLIER", "3.0"))
CONSENSUS_MIN_OUTLIER_THRESHOLD = float(os.getenv("CONSENSUS_MIN_OUTLIER_THRESHOLD", "0.5"))

# ==================================================================
# SYNC SCHEDULE CONFIGURATION
# ==================================================================
SYNC_NBA_STATS_INTERVAL_HOURS = int(os.getenv("SYNC_NBA_STATS_INTERVAL_HOURS", "2"))
SYNC_ODDS_INTERVAL_MINUTES = int(os.getenv("SYNC_ODDS_INTERVAL_MINUTES", "30"))
COMPUTE_RESULTS_INTERVAL_HOURS = int(os.getenv("COMPUTE_RESULTS_INTERVAL_HOURS", "1"))

# ==================================================================
# TIMEZONE
# ==================================================================
TIMEZONE = os.getenv("TZ", "America/Chicago")

# ==================================================================
# LOGGING
# ==================================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==================================================================
# FASTAPI CONFIGURATION
# ==================================================================
API_TITLE = "NBA Betting Analytics API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "Backend API for NBA betting analytics platform"

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
