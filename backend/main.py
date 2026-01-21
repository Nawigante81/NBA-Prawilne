import os
import asyncio
import base64
import contextlib
import hmac
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, date
import statistics
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import anyio
# Import supabase through isolated client to avoid conflicts
from supabase_client import create_isolated_supabase_client, get_supabase_config
from typing import Any as Client  # Use Any as Client placeholder to fix typing
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

# Temporarily use mock implementations to avoid httpx_socks conflicts with supabase
# These will be loaded dynamically when needed
def scrape_all_data(*args, **kwargs):
    """Mock scraper function - will be replaced with real implementation"""
    logger.info("Using mock scraper - anti-bot functionality disabled for now")
    return {}

class NBAReportGenerator:
    """Mock report generator - will be replaced with real implementation"""
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        logger.info("Using mock report generator")
    
    async def generate_750am_report(self):
        return {"report_type": "750am_mock", "timestamp": datetime.now().isoformat()}
    
    async def generate_800am_report(self):
        return {"report_type": "800am_mock", "timestamp": datetime.now().isoformat()}
    
    async def generate_1100am_report(self):
        return {"report_type": "1100am_mock", "timestamp": datetime.now().isoformat()}
    
    async def _bulls_gameday_analysis(self):
        return {"mock": "bulls_analysis"}
    
    async def _comprehensive_betting_strategy(self):
        return {"mock": "betting_strategy"}
    
    def calculate_kelly_criterion(self, prob, odds):
        return max(0, min((prob * odds - 1) / (odds - 1) * 0.25, 0.25))
    
    def format_betting_slip(self, bets, stake):
        return {"mock": "betting_slip", "total_stake": stake}
    
    async def save_report(self, report, report_type):
        """Mock save report"""
        logger.info(f"Mock saving report: {report_type}")
        return True
        
        def calculate_roi_projection(self, history):
            return {"roi": 0, "total_bets": 0, "win_rate": 0}
        
        async def identify_arbitrage_opportunities(self, odds):
            return []

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Silence overly-verbose HTTP client logs (e.g. "HTTP Request: ... 200 OK")
# Some environments attach handlers that still emit these at INFO, so disable explicitly.
for logger_name in ("httpx", "httpcore"):
    _logger = logging.getLogger(logger_name)
    _logger.setLevel(logging.WARNING)
    _logger.propagate = False
    _logger.disabled = True

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_env_backend = os.path.join(os.path.dirname(__file__), ".env")
_env_prod = os.path.join(_project_root, ".env.production")
_env_dev = os.path.join(_project_root, ".env")
_node_env = (os.getenv("NODE_ENV") or "").strip().lower()
if os.path.isfile(_env_backend):
    load_dotenv(_env_backend, override=False)
if _node_env == "production" and os.path.isfile(_env_prod):
    load_dotenv(_env_prod, override=False)
elif os.path.isfile(_env_dev):
    load_dotenv(_env_dev, override=False)
elif os.path.isfile(_env_prod):
    load_dotenv(_env_prod, override=False)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
SCRAPE_INTERVAL_SECONDS = 6 * 60 * 60
CHICAGO_TZ = pytz.timezone("America/Chicago")


def _load_auth_users() -> dict[str, dict[str, str]]:
    admin_user = os.getenv("APP_AUTH_ADMIN_USER", "admin").strip() or "admin"
    admin_password = os.getenv("APP_AUTH_ADMIN_PASSWORD", "Kanciastoporty1202!")
    marek_user = os.getenv("APP_AUTH_MAREK_USER", "Marek").strip() or "Marek"
    marek_password = os.getenv("APP_AUTH_MAREK_PASSWORD", "Kordon2000!")
    return {
        admin_user: {"password": admin_password, "role": "admin"},
        marek_user: {"password": marek_password, "role": "user"},
    }


AUTH_USERS = _load_auth_users()
AUTH_EXEMPT_PATHS = {
    "/health",
    "/api/auth/login",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def _verify_basic_auth(auth_header: str | None) -> dict[str, str] | None:
    if not auth_header:
        return None
    if not auth_header.lower().startswith("basic "):
        return None
    encoded = auth_header.split(" ", 1)[1].strip()
    if not encoded:
        return None
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except Exception:
        return None
    if ":" not in decoded:
        return None
    username, password = decoded.split(":", 1)
    user = AUTH_USERS.get(username)
    if not user:
        return None
    if not hmac.compare_digest(password, user.get("password", "")):
        return None
    return {"username": username, "role": user.get("role", "user")}


async def _verify_bearer_token(auth_header: str | None) -> dict[str, str] | None:
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        return None
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {token}", "apikey": SUPABASE_ANON_KEY},
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        email = data.get("email")
        user_id = data.get("id")
        return {"username": email or user_id or "user", "role": "user"}
    except Exception:
        return None


class LoginRequest(BaseModel):
    username: str
    password: str


def chicago_day_bounds_utc(day: date | None = None) -> tuple[datetime, datetime]:
    """Return [start,end) bounds for a Chicago calendar day converted to UTC.

    - 'day' is interpreted in America/Chicago.
    - Returned datetimes are timezone-aware in UTC.
    """
    if day is None:
        day = datetime.now(CHICAGO_TZ).date()

    start_local_naive = datetime.combine(day, datetime.min.time())
    start_local = CHICAGO_TZ.localize(start_local_naive)
    end_local = start_local + timedelta(days=1)

    start_utc = start_local.astimezone(pytz.UTC)
    end_utc = end_local.astimezone(pytz.UTC)
    return start_utc, end_utc


def _safe_float(value) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        if f <= 0:
            return None
        return f
    except Exception:
        return None


def _compute_no_vig_consensus_probs(
    h2h_rows: list[dict],
    home_team: str,
    away_team: str,
) -> tuple[float, float] | None:
    """Compute consensus no-vig probabilities from per-book prices.

    Returns (p_home, p_away) as decimals in [0,1], or None if insufficient data.
    Assumes decimal odds.
    """
    by_book: dict[str, dict[str, float]] = {}

    for row in h2h_rows:
        team = (row.get("team") or "").strip()
        price = _safe_float(row.get("price"))
        if not team or price is None:
            continue

        book_key = (row.get("bookmaker_key") or row.get("bookmaker_title") or "unknown").strip()
        by_book.setdefault(book_key, {})[team] = price

    home_probs: list[float] = []
    away_probs: list[float] = []
    for book, prices in by_book.items():
        if home_team not in prices or away_team not in prices:
            continue
        home_price = prices[home_team]
        away_price = prices[away_team]
        p_home = 1.0 / home_price
        p_away = 1.0 / away_price
        total = p_home + p_away
        if total <= 0:
            continue
        home_probs.append(p_home / total)
        away_probs.append(p_away / total)

    if not home_probs or not away_probs:
        return None

    # Use mean consensus; easy to reason about and stable.
    return (statistics.mean(home_probs), statistics.mean(away_probs))


def _best_price_for_team(h2h_rows: list[dict], team: str) -> tuple[float, str] | None:
    """Return (best_decimal_price, bookmaker_title) for team from h2h rows."""
    best: tuple[float, str] | None = None
    team_norm = team.strip().lower()
    for row in h2h_rows:
        row_team = (row.get("team") or "").strip()
        if row_team.strip().lower() != team_norm:
            continue
        price = _safe_float(row.get("price"))
        if price is None:
            continue
        book = (row.get("bookmaker_title") or row.get("bookmaker_key") or "").strip() or "unknown"
        if best is None or price > best[0]:
            best = (price, book)
    return best


def _parse_minutes_to_float(minutes_value: str | None) -> float | None:
    """Parse NBA minutes strings like '34:22' into float minutes."""
    if not minutes_value:
        return None
    s = str(minutes_value).strip()
    if not s:
        return None
    try:
        if ":" in s:
            mm, ss = s.split(":", 1)
            return float(mm) + (float(ss) / 60.0)
        return float(s)
    except Exception:
        return None


def _estimate_possessions(fga: float | None, orb: float | None, tov: float | None, fta: float | None) -> float | None:
    if fga is None or orb is None or tov is None or fta is None:
        return None
    # Common approximation used in basketball analytics
    return float(fga) - float(orb) + float(tov) + 0.44 * float(fta)


def _trend_direction(delta: float | None, threshold: float) -> str | None:
    if delta is None:
        return None
    if delta > threshold:
        return "up"
    if delta < -threshold:
        return "down"
    return "stable"


def _format_delta(delta: float | None, *, is_pct: bool = False) -> str | None:
    if delta is None:
        return None
    sign = "+" if delta >= 0 else ""
    if is_pct:
        return f"{sign}{delta * 100.0:.1f}%"
    return f"{sign}{delta:.1f}"


def _matchup_is_home(matchup: str | None) -> bool | None:
    if not matchup:
        return None
    s = str(matchup)
    if "@" in s:
        return False
    if "vs" in s.lower():
        return True
    return None


def _opponent_from_matchup(team_abbrev: str, matchup: str | None) -> str | None:
    if not matchup:
        return None
    s = str(matchup).replace("vs.", "vs").strip()
    team = team_abbrev.strip().upper()
    if "@" in s:
        parts = s.split("@", 1)
        return (parts[1] or "").strip() or None
    if "vs" in s.lower():
        parts = s.lower().split("vs", 1)
        if len(parts) == 2:
            return parts[1].strip().upper() or None
    return None


async def _load_player_season_stats(
    supabase: Client, player_name: str, team_tricode: str | None
) -> dict | None:
    if not player_name:
        return None

    async def _latest_season(for_team: bool) -> str | None:
        def _query():
            q = supabase.table("player_game_stats").select("season_year,game_date")
            q = q.ilike("player_name", player_name)
            if for_team and team_tricode:
                q = q.eq("team_tricode", team_tricode)
            return q.order("game_date", desc=True).limit(1).execute()

        resp = await anyio.to_thread.run_sync(_query)
        row = (resp.data or [None])[0]
        return row.get("season_year") if isinstance(row, dict) else None

    season_year = await _latest_season(for_team=True)
    filter_team = bool(season_year and team_tricode)
    if not season_year:
        season_year = await _latest_season(for_team=False)
        filter_team = False
    if not season_year:
        return None

    async def _season_stats(for_team: bool):
        def _query():
            q = supabase.table("player_game_stats").select(
                "game_id,minutes,points,rebounds_total,assists,steals,blocks,turnovers,"
                "field_goals_made,field_goals_attempted,three_pointers_made,three_pointers_attempted,"
                "free_throws_made,free_throws_attempted"
            )
            q = q.ilike("player_name", player_name).eq("season_year", season_year)
            if for_team and team_tricode:
                q = q.eq("team_tricode", team_tricode)
            return q.order("game_date", desc=True).range(0, 5000).execute()

        return await anyio.to_thread.run_sync(_query)

    stats_resp = await _season_stats(for_team=filter_team)
    if filter_team and not (stats_resp.data or []):
        stats_resp = await _season_stats(for_team=False)
    rows = stats_resp.data or []
    if not rows:
        return None

    games: set[str] = set()
    totals = {
        "points": 0.0,
        "rebounds": 0.0,
        "assists": 0.0,
        "steals": 0.0,
        "blocks": 0.0,
        "turnovers": 0.0,
        "minutes": 0.0,
        "fgm": 0.0,
        "fga": 0.0,
        "tpm": 0.0,
        "tpa": 0.0,
        "ftm": 0.0,
        "fta": 0.0,
    }

    for r in rows:
        gid = r.get("game_id")
        if gid:
            games.add(str(gid))
        totals["points"] += float(r.get("points") or 0)
        totals["rebounds"] += float(r.get("rebounds_total") or 0)
        totals["assists"] += float(r.get("assists") or 0)
        totals["steals"] += float(r.get("steals") or 0)
        totals["blocks"] += float(r.get("blocks") or 0)
        totals["turnovers"] += float(r.get("turnovers") or 0)
        totals["fgm"] += float(r.get("field_goals_made") or 0)
        totals["fga"] += float(r.get("field_goals_attempted") or 0)
        totals["tpm"] += float(r.get("three_pointers_made") or 0)
        totals["tpa"] += float(r.get("three_pointers_attempted") or 0)
        totals["ftm"] += float(r.get("free_throws_made") or 0)
        totals["fta"] += float(r.get("free_throws_attempted") or 0)
        minutes = _parse_minutes_to_float(r.get("minutes"))
        if minutes is not None:
            totals["minutes"] += float(minutes)

    games_played = len(games)
    if games_played <= 0:
        return None

    def _pct(made: float, att: float) -> float | None:
        if att <= 0:
            return None
        return made / att

    return {
        "season_year": season_year,
        "games_played": games_played,
        "ppg": totals["points"] / games_played,
        "rpg": totals["rebounds"] / games_played,
        "apg": totals["assists"] / games_played,
        "spg": totals["steals"] / games_played,
        "bpg": totals["blocks"] / games_played,
        "tov": totals["turnovers"] / games_played,
        "mpg": totals["minutes"] / games_played if totals["minutes"] > 0 else None,
        "fg_percentage": _pct(totals["fgm"], totals["fga"]),
        "three_point_percentage": _pct(totals["tpm"], totals["tpa"]),
        "ft_percentage": _pct(totals["ftm"], totals["fta"]),
    }


async def _load_player_recent_games(
    supabase: Client, player_name: str, team_tricode: str | None, limit: int = 10
) -> list[dict] | None:
    if not player_name:
        return None

    async def _latest_season(for_team: bool) -> str | None:
        def _query():
            q = supabase.table("player_game_stats").select("season_year,game_date")
            q = q.ilike("player_name", player_name)
            if for_team and team_tricode:
                q = q.eq("team_tricode", team_tricode)
            return q.order("game_date", desc=True).limit(1).execute()

        resp = await anyio.to_thread.run_sync(_query)
        row = (resp.data or [None])[0]
        return row.get("season_year") if isinstance(row, dict) else None

    season_year = await _latest_season(for_team=True)
    filter_team = bool(season_year and team_tricode)
    if not season_year:
        season_year = await _latest_season(for_team=False)
        filter_team = False
    if not season_year:
        return None

    async def _recent(for_team: bool):
        def _query():
            q = supabase.table("player_game_stats").select(
                "game_date,points,rebounds_total,assists,steals,blocks,turnovers,minutes"
            )
            q = q.ilike("player_name", player_name).eq("season_year", season_year)
            if for_team and team_tricode:
                q = q.eq("team_tricode", team_tricode)
            return q.order("game_date", desc=True).limit(limit).execute()

        return await anyio.to_thread.run_sync(_query)

    recent_resp = await _recent(for_team=filter_team)
    if filter_team and not (recent_resp.data or []):
        recent_resp = await _recent(for_team=False)
    rows = recent_resp.data or []
    if not rows:
        return None

    games: list[dict] = []
    for r in reversed(rows):
        games.append(
            {
                "game_date": r.get("game_date"),
                "points": r.get("points"),
                "rebounds": r.get("rebounds_total"),
                "assists": r.get("assists"),
                "steals": r.get("steals"),
                "blocks": r.get("blocks"),
                "turnovers": r.get("turnovers"),
                "minutes": r.get("minutes"),
            }
        )
    return games


async def _load_team_games_from_stats(
    supabase: Client, team_abbrev: str, max_games: int = 82
) -> tuple[list[dict], str | None]:
    """Load per-game team/opponent totals from player_game_stats (real data only)."""
    latest_resp = await anyio.to_thread.run_sync(
        lambda: supabase.table("player_game_stats")
        .select("season_year,game_date")
        .eq("team_tricode", team_abbrev)
        .order("game_date", desc=True)
        .limit(1)
        .execute()
    )
    latest_row = (latest_resp.data or [None])[0]
    season_year = latest_row.get("season_year") if isinstance(latest_row, dict) else None
    if not season_year:
        return [], None

    # NOTE: player_game_stats is player-level. Keep this query as light as possible
    # because it is called repeatedly (e.g., for all teams).
    # Heuristic: ~15 players logged per game, so fetch ~max_games*20 rows to reliably
    # cover max_games distinct game_ids without scanning thousands of rows.
    per_game_player_rows = int(os.getenv("TEAM_GAMES_PLAYER_ROW_MULT", "20"))
    team_rows_limit = max(200, max_games * max(10, per_game_player_rows))

    team_rows_resp = await anyio.to_thread.run_sync(
        lambda limit=team_rows_limit: supabase.table("player_game_stats")
        .select("game_id,game_date,matchup")
        .eq("team_tricode", team_abbrev)
        .eq("season_year", season_year)
        .order("game_date", desc=True)
        .limit(limit)
        .execute()
    )
    team_rows = team_rows_resp.data or []
    if not team_rows:
        return [], season_year

    game_ids: list[str] = []
    matchup_by_game: dict[str, str | None] = {}
    date_by_game: dict[str, str | None] = {}
    seen: set[str] = set()
    for r in team_rows:
        gid = r.get("game_id")
        if not gid or gid in seen:
            continue
        seen.add(gid)
        game_ids.append(gid)
        matchup_by_game[gid] = r.get("matchup")
        date_by_game[gid] = r.get("game_date")
        if len(game_ids) >= max_games:
            break

    if not game_ids:
        return [], season_year

    # Heuristic: both teams combined (~25-35 player rows per game). Keep a hard cap to
    # avoid huge table scans on large/poorly-indexed datasets.
    all_rows_mult = int(os.getenv("TEAM_GAMES_ALL_PLAYER_ROW_MULT", "50"))
    all_rows_limit = max(500, max_games * max(25, all_rows_mult))

    all_rows_resp = await anyio.to_thread.run_sync(
        lambda gids=game_ids, limit=all_rows_limit: supabase.table("player_game_stats")
        .select(
            "game_id,team_tricode,points,field_goals_made,field_goals_attempted,"
            "three_pointers_made,three_pointers_attempted,free_throws_made,free_throws_attempted,"
            "rebounds_offensive,turnovers"
        )
        .in_("game_id", gids)
        .eq("season_year", season_year)
        .limit(limit)
        .execute()
    )
    all_rows = all_rows_resp.data or []

    def _init_totals() -> dict:
        return {
            "points": 0.0,
            "fgm": 0.0,
            "fga": 0.0,
            "tpm": 0.0,
            "tpa": 0.0,
            "ftm": 0.0,
            "fta": 0.0,
            "orb": 0.0,
            "tov": 0.0,
        }

    totals_by_game_team: dict[str, dict[str, dict]] = {}
    for r in all_rows:
        gid = r.get("game_id")
        tcode = r.get("team_tricode")
        if not gid or not tcode:
            continue
        g = totals_by_game_team.setdefault(gid, {})
        tot = g.setdefault(tcode, _init_totals())
        tot["points"] += float(r.get("points") or 0)
        tot["fgm"] += float(r.get("field_goals_made") or 0)
        tot["fga"] += float(r.get("field_goals_attempted") or 0)
        tot["tpm"] += float(r.get("three_pointers_made") or 0)
        tot["tpa"] += float(r.get("three_pointers_attempted") or 0)
        tot["ftm"] += float(r.get("free_throws_made") or 0)
        tot["fta"] += float(r.get("free_throws_attempted") or 0)
        tot["orb"] += float(r.get("rebounds_offensive") or 0)
        tot["tov"] += float(r.get("turnovers") or 0)

    games_ordered: list[dict] = []
    for gid in game_ids:
        teams_totals = totals_by_game_team.get(gid) or {}
        team_totals = teams_totals.get(team_abbrev)
        if not team_totals:
            continue
        opp_codes = [k for k in teams_totals.keys() if k != team_abbrev]
        opp_totals = teams_totals.get(opp_codes[0]) if opp_codes else None
        games_ordered.append(
            {
                "game_id": gid,
                "game_date": date_by_game.get(gid),
                "matchup": matchup_by_game.get(gid),
                "team": team_totals,
                "opp": opp_totals,
            }
        )

    return games_ordered, season_year


def _summarize_team_games(team_abbrev: str, games_ordered: list[dict]) -> dict:
    if not games_ordered:
        return {
            "season_stats": None,
            "recent_form": None,
            "strength_rating": None,
        }

    wins = losses = 0
    home_wins = home_losses = 0
    away_wins = away_losses = 0
    points_for: list[float] = []
    points_against: list[float] = []
    off_rtg_vals: list[float] = []
    def_rtg_vals: list[float] = []

    for g in games_ordered:
        team_pts = g["team"]["points"]
        opp_pts = (g["opp"] or {}).get("points")
        if opp_pts is None:
            continue
        points_for.append(float(team_pts))
        points_against.append(float(opp_pts))
        is_win = float(team_pts) > float(opp_pts)
        if is_win:
            wins += 1
        else:
            losses += 1

        is_home = _matchup_is_home(g.get("matchup"))
        if is_home is True:
            if is_win:
                home_wins += 1
            else:
                home_losses += 1
        elif is_home is False:
            if is_win:
                away_wins += 1
            else:
                away_losses += 1

        poss = _estimate_possessions(
            g["team"]["fga"], g["team"]["orb"], g["team"]["tov"], g["team"]["fta"]
        )
        if poss and poss > 0:
            off_rtg_vals.append(100.0 * float(team_pts) / poss)
            def_rtg_vals.append(100.0 * float(opp_pts) / poss)

    def _mean(vals: list[float]) -> float | None:
        if not vals:
            return None
        return float(statistics.mean(vals))

    points_per_game = _mean(points_for)
    points_allowed = _mean(points_against)
    off_rtg = _mean(off_rtg_vals)
    def_rtg = _mean(def_rtg_vals)
    net_rtg = None if off_rtg is None or def_rtg is None else off_rtg - def_rtg
    total_games = wins + losses
    win_pct = (wins / total_games) if total_games > 0 else None

    def _record_string(w: int, l: int) -> str | None:
        if (w + l) == 0:
            return None
        return f"{w}-{l}"

    last_10 = games_ordered[:10]
    last_10_w = sum(1 for g in last_10 if (g.get("opp") or {}).get("points") is not None and g["team"]["points"] > float(g["opp"]["points"]))
    last_10_l = sum(1 for g in last_10 if (g.get("opp") or {}).get("points") is not None and g["team"]["points"] <= float(g["opp"]["points"]))

    last_5 = games_ordered[:5]
    last_5_w = sum(1 for g in last_5 if (g.get("opp") or {}).get("points") is not None and g["team"]["points"] > float(g["opp"]["points"]))
    last_5_l = sum(1 for g in last_5 if (g.get("opp") or {}).get("points") is not None and g["team"]["points"] <= float(g["opp"]["points"]))

    strength_rating = None
    if net_rtg is not None:
        strength_rating = max(0.0, min(100.0, round(50.0 + (net_rtg * 2.0), 1)))

    return {
        "season_stats": {
            "wins": wins,
            "losses": losses,
            "win_percentage": win_pct,
            "points_per_game": points_per_game,
            "points_allowed": points_allowed,
            "offensive_rating": off_rtg,
            "defensive_rating": def_rtg,
            "net_rating": net_rtg,
        }
        if total_games > 0
        else None,
        "recent_form": {
            "last_10": _record_string(last_10_w, last_10_l),
            "last_5": _record_string(last_5_w, last_5_l),
            "home_record": _record_string(home_wins, home_losses),
            "away_record": _record_string(away_wins, away_losses),
            "vs_conference": None,
        },
        "strength_rating": strength_rating,
    }


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None


def _betting_cache_expired(computed_at: str | None, ttl_hours: int) -> bool:
    if not computed_at:
        return True
    dt = _parse_iso_datetime(computed_at)
    if not dt:
        return True
    return dt < (datetime.now(dt.tzinfo) - timedelta(hours=ttl_hours))


async def _load_betting_cache_map(supabase: Client) -> dict:
    try:
        resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("team_betting_stats")
            .select("*")
            .execute()
        )
        rows = resp.data or []
        return {str(r.get("team_name") or ""): r for r in rows if r.get("team_name")}
    except Exception as e:
        if "team_betting_stats" in str(e):
            logger.warning(f"team_betting_stats cache missing: {e}")
            return {}
        raise


async def _save_betting_cache(supabase: Client, team_name: str, stats: dict | None, games_count: int | None):
    if not stats or not team_name:
        return
    record = {
        "team_name": team_name,
        "games_count": games_count,
        "ats_record": stats.get("ats_record"),
        "ats_percentage": stats.get("ats_percentage"),
        "over_under": stats.get("over_under"),
        "ou_percentage": stats.get("ou_percentage"),
        "avg_total": stats.get("avg_total"),
        "computed_at": datetime.now().isoformat(),
    }
    await anyio.to_thread.run_sync(
        lambda r=record: supabase.table("team_betting_stats")
        .upsert([r], on_conflict="team_name")
        .execute()
    )
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        return None


async def _find_odds_game_for_result(
    supabase: Client, home_team: str, away_team: str, game_date_value: str | date | None
) -> dict | None:
    if not game_date_value:
        return None
    if isinstance(game_date_value, date):
        d = game_date_value
    else:
        try:
            d = datetime.fromisoformat(str(game_date_value)).date()
        except Exception:
            return None

    start = datetime(d.year, d.month, d.day)
    end = start + timedelta(days=1)

    resp = await anyio.to_thread.run_sync(
        lambda: supabase.table("games")
        .select("id,commence_time,home_team,away_team")
        .eq("home_team", home_team)
        .eq("away_team", away_team)
        .gte("commence_time", start.isoformat())
        .lt("commence_time", end.isoformat())
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


def _median_values(values: list[float]) -> float | None:
    clean = [v for v in values if isinstance(v, (int, float))]
    if not clean:
        return None
    return float(statistics.median(clean))


async def _load_closing_lines(
    supabase: Client, game_id: str, commence_time: str | None
) -> tuple[dict | None, float | None]:
    if not game_id or not commence_time:
        return None, None
    commence_dt = _parse_iso_datetime(commence_time)
    if not commence_dt:
        return None, None

    odds_resp = await anyio.to_thread.run_sync(
        lambda: supabase.table("odds")
        .select("last_update,market_type,team,outcome_name,point")
        .eq("game_id", game_id)
        .in_("market_type", ["spread", "totals"])
        .execute()
    )
    rows = odds_resp.data or []
    if not rows:
        return None, None

    latest_dt = None
    latest_str = None
    for r in rows:
        lu = r.get("last_update")
        lu_dt = _parse_iso_datetime(lu)
        if not lu_dt or lu_dt > commence_dt:
            continue
        if latest_dt is None or lu_dt > latest_dt:
            latest_dt = lu_dt
            latest_str = lu

    if not latest_str:
        return None, None

    closing_rows = [r for r in rows if r.get("last_update") == latest_str]
    spread_by_team: dict[str, list[float]] = {}
    for r in closing_rows:
        if r.get("market_type") != "spread":
            continue
        team = (r.get("team") or "").strip()
        if not team:
            continue
        point = r.get("point")
        try:
            val = float(point)
        except Exception:
            continue
        spread_by_team.setdefault(team, [])
        spread_by_team[team].append(val)

    spread_median: dict[str, float] = {}
    for team, vals in spread_by_team.items():
        med = _median_values(vals)
        if med is not None:
            spread_median[team] = med

    total_lines = []
    for r in closing_rows:
        if r.get("market_type") != "totals":
            continue
        if (r.get("outcome_name") or "").lower() != "over":
            continue
        try:
            total_lines.append(float(r.get("point")))
        except Exception:
            continue

    total_line = _median_values(total_lines)
    return spread_median, total_line


async def _compute_betting_stats(
    supabase: Client, team_full_name: str, max_games: int = 20
) -> dict | None:
    if not team_full_name:
        return None
    try:
        results_resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("game_results")
            .select("*")
            .or_(f"home_team.eq.{team_full_name},away_team.eq.{team_full_name}")
            .order("game_date", desc=True)
            .limit(max_games)
            .execute()
        )
        results = results_resp.data or []
        if not results:
            return None
    except Exception as e:
        # Missing table or schema cache should not break the endpoint.
        if "game_results" in str(e):
            logger.warning(f"game_results unavailable, skipping betting stats: {e}")
            return None
        raise

    ats_w = ats_l = ats_p = 0
    ou_o = ou_u = ou_p = 0
    total_lines: list[float] = []
    games_count = 0

    for r in results:
        home_team = r.get("home_team")
        away_team = r.get("away_team")
        home_score = r.get("home_score")
        away_score = r.get("away_score")
        if home_score is None or away_score is None:
            continue

        game = await _find_odds_game_for_result(
            supabase, home_team, away_team, r.get("game_date")
        )
        if not game:
            continue
        spread_map, total_line = await _load_closing_lines(
            supabase, game.get("id"), game.get("commence_time")
        )
        if not spread_map and total_line is None:
            continue

        team_is_home = team_full_name == home_team
        team_score = float(home_score)
        opp_score = float(away_score)
        if not team_is_home:
            team_score, opp_score = opp_score, team_score

        spread = None
        if spread_map:
            spread = spread_map.get(team_full_name)

        if spread is not None:
            adj = team_score + float(spread)
            if adj > opp_score:
                ats_w += 1
            elif adj < opp_score:
                ats_l += 1
            else:
                ats_p += 1
            games_count += 1

        if total_line is not None:
            total_lines.append(float(total_line))
            total_score = float(home_score) + float(away_score)
            if total_score > float(total_line):
                ou_o += 1
            elif total_score < float(total_line):
                ou_u += 1
            else:
                ou_p += 1

    ats_den = ats_w + ats_l
    ou_den = ou_o + ou_u

    return {
        "ats_record": f"{ats_w}-{ats_l}-{ats_p}",
        "ats_percentage": (ats_w / ats_den) if ats_den > 0 else None,
        "over_under": f"{ou_o}-{ou_u}-{ou_p}",
        "ou_percentage": (ou_o / ou_den) if ou_den > 0 else None,
        "avg_total": float(statistics.mean(total_lines)) if total_lines else None,
        "games_count": games_count,
    }


async def scrape_loop(supabase: Client, stop_evt: asyncio.Event):
    """Background loop to scrape data at regular intervals"""
    try:
        while not stop_evt.is_set():
            await scrape_all_data(supabase)
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=SCRAPE_INTERVAL_SECONDS)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        print("Scrape loop cancelled")
        raise


async def generate_750am_report(supabase: Client):
    """Generate 7:50 AM report"""
    try:
        print(f"[{datetime.now().isoformat()}] Generating 7:50 AM report...")
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_750am_report()
        await generator.save_report(report, "750am_previous_day")
        print(f"[{datetime.now().isoformat()}] 7:50 AM report completed")
    except Exception as e:
        print(f"Error generating 7:50 AM report: {e}")


async def generate_800am_report(supabase: Client):
    """Generate 8:00 AM report"""
    try:
        print(f"[{datetime.now().isoformat()}] Generating 8:00 AM report...")
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_800am_report()
        await generator.save_report(report, "800am_morning")
        print(f"[{datetime.now().isoformat()}] 8:00 AM report completed")
    except Exception as e:
        print(f"Error generating 8:00 AM report: {e}")


async def generate_1100am_report(supabase: Client):
    """Generate 11:00 AM report"""
    try:
        print(f"[{datetime.now().isoformat()}] Generating 11:00 AM report...")
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_1100am_report()
        await generator.save_report(report, "1100am_gameday")
        print(f"[{datetime.now().isoformat()}] 11:00 AM report completed")
    except Exception as e:
        print(f"Error generating 11:00 AM report: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app lifecycle - startup and shutdown"""
    # Initialize Supabase client first  
    try:
        if os.getenv("SUPABASE_DISABLED", "false").lower() == "true":
            raise ValueError("Supabase disabled by SUPABASE_DISABLED")

        config = get_supabase_config()
        
        if not config["available"]:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
            
        # Use SERVICE_ROLE_KEY for backend operations (has elevated privileges)
        service_key = config["service_key"] or config["anon_key"]
        supabase = create_isolated_supabase_client(config["url"], service_key)
        app.state.supabase = supabase
        
        if config["service_key"]:
            print("[OK] Starting application with Supabase (Service Role)")
        else:
            print("[WARNING] Starting application with Supabase (Anon Key - limited permissions)")
        
        # Import scrapers after Supabase client is created to avoid conflicts
        try:
            from scrapers import scrape_all_data as real_scrape_all_data
            from scrapers import scrape_recent_results as real_scrape_recent_results
            from reports import NBAReportGenerator as RealNBAReportGenerator
            
            # Replace mock functions with real implementations
            global scrape_all_data, scrape_recent_results, NBAReportGenerator
            scrape_all_data = real_scrape_all_data
            scrape_recent_results = real_scrape_recent_results
            NBAReportGenerator = RealNBAReportGenerator
            print("[OK] Anti-bot scraping system loaded")
            
        except ImportError as ie:
            print(f"[WARNING] Scrapers not available: {ie}")
        
        # Start data scraping on startup (only if enabled). Run in background to avoid blocking server startup.
        if os.getenv("AUTO_SCRAPE_ON_START", "false").lower() == "true":
            asyncio.create_task(scrape_all_data(supabase))
            print("Automatic scraping on startup enabled (background task).")
        else:
            print("Automatic scraping on startup disabled. Use /api/scrape endpoints to trigger manually.")
            
    except Exception as e:
        print(f"[ERROR] Error initializing Supabase: {e}")
        print("[INFO] Running in development mode without Supabase...")
        app.state.supabase = None

    # Set up scheduler for reports if scheduling is enabled (even without Supabase in dev mode)
    scheduler_enabled = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    
    if scheduler_enabled:
        scheduler = AsyncIOScheduler(timezone=CHICAGO_TZ)

        scheduler.add_job(
            generate_750am_report,
            CronTrigger(hour=7, minute=50, timezone=CHICAGO_TZ),
            args=[app.state.supabase],
            id="report_750am"
        )

        scheduler.add_job(
            generate_800am_report,
            CronTrigger(hour=8, minute=0, timezone=CHICAGO_TZ),
            args=[app.state.supabase],
            id="report_800am"
        )

        scheduler.add_job(
            generate_1100am_report,
            CronTrigger(hour=11, minute=0, timezone=CHICAGO_TZ),
            args=[app.state.supabase],
            id="report_1100am"
        )

        if app.state.supabase:
            results_interval_min = int(os.getenv("RESULTS_SCRAPE_INTERVAL_MIN", "60"))
            results_days_back = int(os.getenv("RESULTS_SCRAPE_DAYS_BACK", "3"))

            async def _scrape_results_job():
                if app.state.supabase:
                    await scrape_recent_results(app.state.supabase, days_back=results_days_back)

            scheduler.add_job(
                _scrape_results_job,
                IntervalTrigger(minutes=results_interval_min),
                id="results_scrape",
                replace_existing=True,
            )

        scheduler.start()
        print("[OK] Scheduler enabled and running")

        if app.state.supabase:
            app.state.stop_evt = asyncio.Event()
            task = asyncio.create_task(scrape_loop(app.state.supabase, app.state.stop_evt))
            print("[OK] Background scraping task started")
        else:
            print("[WARNING] Background scraping disabled - no Supabase connection")
            task = None
    else:
        print("[ERROR] Scheduler disabled - set ENABLE_SCHEDULER=true to enable")
        scheduler = None
        task = None

    try:
        yield
    finally:
        print("Shutting down application...")
        if hasattr(app.state, 'stop_evt') and app.state.stop_evt:
            app.state.stop_evt.set()
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        if scheduler:
            scheduler.shutdown(wait=False)


app = FastAPI(title="NBA Analysis API", lifespan=lifespan)

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS":
        return await call_next(request)
    if path.startswith("/api") and path not in AUTH_EXEMPT_PATHS:
        auth_header = request.headers.get("authorization")
        user = _verify_basic_auth(auth_header)
        if not user:
            user = await _verify_bearer_token(auth_header)
        if not user:
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
        request.state.user = user
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "supabase_connected": bool(getattr(app.state, "supabase", None)),
    }


@app.post("/api/auth/login")
async def login(payload: LoginRequest):
    """Validate username/password and return basic profile info."""
    user = AUTH_USERS.get(payload.username)
    if not user or not hmac.compare_digest(payload.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True, "username": payload.username, "role": user.get("role", "user")}


@app.get("/api/teams")
async def get_teams():
    """Get all teams"""
    try:
        supabase = app.state.supabase
        if supabase:
            response = await anyio.to_thread.run_sync(
                lambda: supabase.table("teams").select("*").execute()
            )
            return {"teams": response.data}

        # Supabase unavailable: do not fabricate data.
        return {"teams": []}
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/games/today")
async def get_today_games(verify: bool = False):
    """Get today's games"""
    try:
        supabase = app.state.supabase
        if supabase:
            start_utc, end_utc = chicago_day_bounds_utc()

            # Determine the Chicago calendar day we are answering for
            chicago_day = datetime.now(CHICAGO_TZ).date()

            response = await anyio.to_thread.run_sync(
                lambda: supabase.table("games")
                .select("*")
                .gte("commence_time", start_utc.isoformat())
                .lt("commence_time", end_utc.isoformat())
                .execute()
            )

            games = response.data or []

            # Optional verification against Basketball-Reference schedule.
            # If verification fails (blocked/unavailable), fall back to unfiltered list.
            do_verify = verify or os.getenv("VERIFY_SCHEDULE_BREF", "false").lower() == "true"
            if do_verify and games:
                try:
                    from scrapers import get_basketball_reference_games_for_date

                    bref_games = await get_basketball_reference_games_for_date(chicago_day)
                    if bref_games:
                        allowed = {
                            (
                                (g.get("away_team") or "").strip().lower(),
                                (g.get("home_team") or "").strip().lower(),
                            )
                            for g in bref_games
                        }
                        games = [
                            g
                            for g in games
                            if (
                                (g.get("away_team") or "").strip().lower(),
                                (g.get("home_team") or "").strip().lower(),
                            )
                            in allowed
                        ]
                except Exception as e:
                    logger.warning(f"Schedule verification failed: {e}")

            return {"games": games}

        # Supabase unavailable: do not fabricate data.
        return {"games": []}
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/odds/{game_id}")
async def get_game_odds(game_id: str):
    """Get odds for a specific game"""
    try:
        supabase = app.state.supabase
        if not supabase:
            return {"odds": []}
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("odds").select("*").eq("game_id", game_id).execute()
        )
        return {"odds": response.data}
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/focus-teams/today")
async def get_focus_teams_today(limit: int = 5):
    """Return teams with best moneyline 'edge' today.

    Edge is computed from market odds only:
    - Build a no-vig consensus win probability from per-book prices.
    - Take the best available (highest) decimal moneyline price for each team.
    - Edge (EV) = p_consensus * best_price - 1
    """
    try:
        supabase = app.state.supabase
        if not supabase:
            return {"teams": []}

        start_utc, end_utc = chicago_day_bounds_utc()

        games_resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("games")
            .select("id,home_team,away_team,commence_time")
            .gte("commence_time", start_utc.isoformat())
            .lt("commence_time", end_utc.isoformat())
            .execute()
        )

        games = games_resp.data or []
        if not games:
            return {"teams": []}

        focus_candidates: list[dict] = []

        for game in games:
            game_id = game.get("id")
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            commence_time = game.get("commence_time")
            if not game_id or not home_team or not away_team:
                continue

            odds_resp = await anyio.to_thread.run_sync(
                lambda gid=game_id: supabase.table("odds")
                .select("bookmaker_key,bookmaker_title,market_type,team,price")
                .eq("game_id", gid)
                .eq("market_type", "h2h")
                .execute()
            )
            h2h_rows = odds_resp.data or []
            if not h2h_rows:
                continue

            consensus = _compute_no_vig_consensus_probs(h2h_rows, home_team, away_team)
            if not consensus:
                continue
            p_home, p_away = consensus

            home_best = _best_price_for_team(h2h_rows, home_team)
            away_best = _best_price_for_team(h2h_rows, away_team)
            if not home_best or not away_best:
                continue

            home_price, home_book = home_best
            away_price, away_book = away_best

            home_edge = p_home * home_price - 1.0
            away_edge = p_away * away_price - 1.0

            focus_candidates.append(
                {
                    "team": home_team,
                    "opponent": away_team,
                    "game_id": game_id,
                    "commence_time": commence_time,
                    "best_price": home_price,
                    "best_book": home_book,
                    "consensus_prob": p_home,
                    "edge": home_edge,
                }
            )
            focus_candidates.append(
                {
                    "team": away_team,
                    "opponent": home_team,
                    "game_id": game_id,
                    "commence_time": commence_time,
                    "best_price": away_price,
                    "best_book": away_book,
                    "consensus_prob": p_away,
                    "edge": away_edge,
                }
            )

        # Sort by best edge first; show positives if any exist.
        positives = [c for c in focus_candidates if (c.get("edge") or 0) > 0]
        ranked = sorted((positives or focus_candidates), key=lambda x: x.get("edge") or -999, reverse=True)

        try:
            limit_int = int(limit)
        except Exception:
            limit_int = 5
        limit_int = max(1, min(limit_int, 20))

        return {"teams": ranked[:limit_int]}

    except Exception as e:
        logger.error(f"Error computing focus teams: {e}")
        return {"error": str(e)}, 500


@app.get("/api/players")
async def get_all_players(
    team: str = None,
    position: str = None,
    active: bool = True,
    include_stats: bool = False,
):
    """Get all players with optional filters"""
    try:
        supabase = app.state.supabase
        if supabase:
            query = supabase.table("players").select("""
                *,
                teams!players_team_id_fkey (
                    abbreviation,
                    full_name,
                    city,
                    name
                )
            """)
            
            if team:
                query = query.eq("team_abbreviation", team.upper())
            if position:
                query = query.ilike("position", f"%{position}%")
            if active is not None:
                query = query.eq("is_active", active)
                
            # Order by team, then by jersey number
            query = query.order("team_abbreviation").order("jersey_number")
            
            response = await anyio.to_thread.run_sync(lambda: query.execute())
            players = response.data or []

            if include_stats and players:
                try:
                    latest_resp = await anyio.to_thread.run_sync(
                        lambda: supabase.table("player_game_stats")
                        .select("season_year,game_date")
                        .order("game_date", desc=True)
                        .limit(1)
                        .execute()
                    )
                    latest_row = (latest_resp.data or [None])[0]
                    season_year = latest_row.get("season_year") if isinstance(latest_row, dict) else None

                    if season_year:
                        stats_resp = await anyio.to_thread.run_sync(
                            lambda: supabase.table("player_game_stats")
                            .select(
                                "player_id,player_name,team_tricode,game_id,minutes,points,rebounds_total,assists,steals,"
                                "blocks,turnovers,field_goals_made,field_goals_attempted,three_pointers_made,"
                                "three_pointers_attempted,free_throws_made,free_throws_attempted"
                            )
                            .eq("season_year", season_year)
                            .range(0, 100000)
                            .execute()
                        )
                        rows = stats_resp.data or []
                        stats_by_pid: dict[int, dict] = {}
                        name_team_pid_counts: dict[tuple[str, str], dict[int, int]] = {}
                        name_pid_counts: dict[str, dict[int, int]] = {}
                        for r in rows:
                            name = (r.get("player_name") or "").strip()
                            if not name:
                                continue
                            pid = r.get("player_id")
                            if pid is None:
                                continue
                            try:
                                pid_int = int(pid)
                            except Exception:
                                continue
                            team_code = (r.get("team_tricode") or "").strip().upper()

                            entry = stats_by_pid.setdefault(
                                pid_int,
                                {
                                    "games": set(),
                                    "points": 0.0,
                                    "rebounds": 0.0,
                                    "assists": 0.0,
                                    "steals": 0.0,
                                    "blocks": 0.0,
                                    "turnovers": 0.0,
                                    "minutes": 0.0,
                                    "fgm": 0.0,
                                    "fga": 0.0,
                                    "tpm": 0.0,
                                    "tpa": 0.0,
                                    "ftm": 0.0,
                                    "fta": 0.0,
                                },
                            )
                            gid = r.get("game_id")
                            if gid:
                                entry["games"].add(str(gid))
                            entry["points"] += float(r.get("points") or 0)
                            entry["rebounds"] += float(r.get("rebounds_total") or 0)
                            entry["assists"] += float(r.get("assists") or 0)
                            entry["steals"] += float(r.get("steals") or 0)
                            entry["blocks"] += float(r.get("blocks") or 0)
                            entry["turnovers"] += float(r.get("turnovers") or 0)
                            entry["fgm"] += float(r.get("field_goals_made") or 0)
                            entry["fga"] += float(r.get("field_goals_attempted") or 0)
                            entry["tpm"] += float(r.get("three_pointers_made") or 0)
                            entry["tpa"] += float(r.get("three_pointers_attempted") or 0)
                            entry["ftm"] += float(r.get("free_throws_made") or 0)
                            entry["fta"] += float(r.get("free_throws_attempted") or 0)
                            minutes = _parse_minutes_to_float(r.get("minutes"))
                            if minutes is not None:
                                entry["minutes"] += float(minutes)

                            if team_code:
                                key = (name, team_code)
                                name_team_pid_counts.setdefault(key, {})
                                name_team_pid_counts[key][pid_int] = name_team_pid_counts[key].get(pid_int, 0) + 1
                            name_pid_counts.setdefault(name, {})
                            name_pid_counts[name][pid_int] = name_pid_counts[name].get(pid_int, 0) + 1

                        computed_stats: dict[int, dict] = {}

                        def _pct(made: float, att: float) -> float | None:
                            if att <= 0:
                                return None
                            return made / att

                        for pid_int, data in stats_by_pid.items():
                            games_played = len(data["games"])
                            if games_played <= 0:
                                continue
                            computed_stats[pid_int] = {
                                "season_year": season_year,
                                "games_played": games_played,
                                "ppg": data["points"] / games_played,
                                "rpg": data["rebounds"] / games_played,
                                "apg": data["assists"] / games_played,
                                "spg": data["steals"] / games_played,
                                "bpg": data["blocks"] / games_played,
                                "tov": data["turnovers"] / games_played,
                                "mpg": data["minutes"] / games_played if data["minutes"] > 0 else None,
                                "fg_percentage": _pct(data["fgm"], data["fga"]),
                                "three_point_percentage": _pct(data["tpm"], data["tpa"]),
                                "ft_percentage": _pct(data["ftm"], data["fta"]),
                            }

                        def _pick_top(counts: dict[int, int]) -> int | None:
                            if not counts:
                                return None
                            return max(counts.items(), key=lambda x: x[1])[0]

                        name_team_to_pid: dict[tuple[str, str], int] = {}
                        for key, counts in name_team_pid_counts.items():
                            pid_pick = _pick_top(counts)
                            if pid_pick is not None:
                                name_team_to_pid[key] = pid_pick

                        name_to_pid: dict[str, int] = {}
                        for name, counts in name_pid_counts.items():
                            pid_pick = _pick_top(counts)
                            if pid_pick is not None:
                                name_to_pid[name] = pid_pick

                        if computed_stats:
                            for p in players:
                                pname = (p.get("name") or "").strip()
                                if not pname:
                                    continue
                                team_code = (p.get("team_abbreviation") or "").strip().upper()
                                pid_pick = p.get("player_id")
                                if pid_pick is None:
                                    pid_pick = name_team_to_pid.get((pname, team_code)) or name_to_pid.get(pname)
                                    if pid_pick is not None:
                                        p["player_id"] = pid_pick
                                if pid_pick is not None and pid_pick in computed_stats:
                                    p["stats"] = computed_stats[pid_pick]
                except Exception as e:
                    logger.warning(f"Player stats enrichment unavailable: {e}")

            return {"players": players, "count": len(players)}

        # Supabase unavailable: do not fabricate data.
        return {"players": [], "count": 0}
    except Exception as e:
        logger.error(f"Error fetching players: {e}")
        return {"error": str(e)}, 500


@app.get("/api/teams/{team_abbrev}/players")
async def get_team_players(team_abbrev: str):
    """Get all players for a specific team"""
    try:
        supabase = app.state.supabase
        
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("players")
            .select("""
                *,
                teams!players_team_id_fkey (
                    abbreviation,
                    full_name,
                    city,
                    name
                )
            """)
            .eq("team_abbreviation", team_abbrev.upper())
            .eq("is_active", True)
            .order("jersey_number")
            .execute()
        )
        
        if not response.data:
            # Check if team exists
            team_check = await anyio.to_thread.run_sync(
                lambda: supabase.table("teams")
                .select("abbreviation")
                .eq("abbreviation", team_abbrev.upper())
                .execute()
            )
            
            if not team_check.data:
                raise HTTPException(status_code=404, detail=f"Team '{team_abbrev}' not found")
            else:
                return {"players": [], "count": 0, "message": f"No active players found for {team_abbrev}"}
        
        return {
            "team": team_abbrev.upper(),
            "players": response.data, 
            "count": len(response.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team players: {e}")
        return {"error": str(e)}, 500


@app.get("/api/players/{player_id}")
async def get_player_details(player_id: str):
    """Get detailed information for a specific player"""
    try:
        supabase = app.state.supabase
        
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("players")
            .select("""
                *,
                teams!players_team_id_fkey (
                    abbreviation,
                    full_name,
                    city,
                    name
                )
            """)
            .eq("id", player_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Player with ID '{player_id}' not found")

        player = response.data[0]
        stats = None
        recent_games = None
        try:
            stats = await _load_player_season_stats(
                supabase,
                player.get("name") or "",
                (player.get("team_abbreviation") or "").upper(),
            )
            recent_games = await _load_player_recent_games(
                supabase,
                player.get("name") or "",
                (player.get("team_abbreviation") or "").upper(),
                limit=10,
            )
        except Exception as e:
            logger.warning(f"Player stats unavailable: {e}")

        bio = {
            "height": player.get("height"),
            "weight": player.get("weight"),
            "birth_date": player.get("birth_date"),
            "experience": player.get("experience"),
            "college": player.get("college"),
        }

        return {"player": {**player, "stats": stats, "bio": bio, "recent_games": recent_games}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player details: {e}")
        return {"error": str(e)}, 500


@app.get("/api/players/search/{name}")
async def search_players_by_name(name: str):
    """Search players by name"""
    try:
        supabase = app.state.supabase
        
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("players")
            .select("""
                *,
                teams!players_team_id_fkey (
                    abbreviation,
                    full_name,
                    city,
                    name
                )
            """)
            .ilike("name", f"%{name}%")
            .eq("is_active", True)
            .order("name")
            .execute()
        )
        
        return {
            "query": name,
            "players": response.data, 
            "count": len(response.data)
        }
    except Exception as e:
        logger.error(f"Error searching players: {e}")
        return {"error": str(e)}, 500


@app.post("/api/scrape/rosters")
async def trigger_roster_scrape(season: str = "2025"):
    """Manually trigger roster scraping for all teams"""
    try:
        from scrapers import scrape_all_team_rosters
        
        supabase = app.state.supabase
        
        # Run roster scraping in background
        asyncio.create_task(scrape_all_team_rosters(supabase, season))
        
        return {
            "message": f"Roster scraping initiated for season {season}",
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress"
        }
    except Exception as e:
        logger.error(f"Error triggering roster scrape: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger roster scraping")


@app.post("/api/scrape/results")
async def trigger_results_scrape(game_date: str):
    """Trigger NBA results scrape for a specific date (YYYY-MM-DD)."""
    try:
        if not getattr(app.state, "supabase", None):
            raise HTTPException(status_code=503, detail="Database not available")
        try:
            target_date = datetime.fromisoformat(game_date).date()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        from scrapers import _fetch_nba_scoreboard

        games = await _fetch_nba_scoreboard(target_date)
        if not games:
            return {"message": "No games found for date", "count": 0}

        records = []
        for g in games:
            if not g.get("home_team") or not g.get("away_team"):
                continue
            status_text = g.get("status") or ""
            is_final = "final" in status_text.lower()
            records.append(
                {
                    "game_id": g.get("game_id"),
                    "game_date": g.get("game_date") or target_date.isoformat(),
                    "home_team": g.get("home_team"),
                    "away_team": g.get("away_team"),
                    "home_score": g.get("home_score"),
                    "away_score": g.get("away_score"),
                    "status": status_text,
                    "finalized_at": datetime.now().isoformat() if is_final else None,
                    "source": "nba_stats",
                }
            )
        if records:
            await anyio.to_thread.run_sync(
                lambda rows=records: app.state.supabase.table("game_results")
                .upsert(rows, on_conflict="game_date,home_team,away_team")
                .execute()
            )

        return {"message": "Results scraped", "count": len(records), "date": target_date.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering results scrape: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape results: {str(e)}")


@app.get("/api/teams/{team_abbrev}/betting-stats")
async def get_team_betting_stats(team_abbrev: str, refresh: bool = False):
    """Get ATS/OU betting stats for a team (cached unless refresh=true)."""
    try:
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")

        team_resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("teams")
            .select("full_name,abbreviation")
            .eq("abbreviation", team_abbrev.upper())
            .single()
            .execute()
        )
        team = team_resp.data
        if not team:
            raise HTTPException(status_code=404, detail=f"Team '{team_abbrev}' not found")

        team_name = team.get("full_name")
        ttl_hours = int(os.getenv("BETTING_CACHE_TTL_HOURS", "6"))

        if not refresh:
            cache_map = await _load_betting_cache_map(supabase)
            cached = cache_map.get(team_name or "")
            if cached and not _betting_cache_expired(cached.get("computed_at"), ttl_hours):
                return {
                    "team": team.get("abbreviation"),
                    "team_name": team_name,
                    "betting_stats": {
                        "ats_record": cached.get("ats_record"),
                        "ats_percentage": cached.get("ats_percentage"),
                        "over_under": cached.get("over_under"),
                        "ou_percentage": cached.get("ou_percentage"),
                        "avg_total": cached.get("avg_total"),
                        "games_count": cached.get("games_count"),
                    },
                    "cached": True,
                    "computed_at": cached.get("computed_at"),
                }

        stats = await _compute_betting_stats(supabase, team_name or "")
        if stats:
            await _save_betting_cache(supabase, team_name or "", stats, stats.get("games_count"))

        return {
            "team": team.get("abbreviation"),
            "team_name": team_name,
            "betting_stats": stats,
            "cached": False,
            "computed_at": datetime.now().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching betting stats for {team_abbrev}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch betting stats")


@app.get("/api/status")
async def get_status():
    """Get application status"""
    return {
        "status": "running",
        "scrape_interval_hours": SCRAPE_INTERVAL_SECONDS / 3600,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/reports/750am")
async def get_750am_report():
    """Get 7:50 AM report (previous day analysis)"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_750am_report()
        return report
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/reports/800am")
async def get_800am_report():
    """Get 8:00 AM report (morning summary)"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_800am_report()
        return report
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/reports/1100am")
async def get_1100am_report():
    """Get 11:00 AM report (game-day scouting)"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        report = await generator.generate_1100am_report()
        return report
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/reports")
async def list_reports(limit: int = 10):
    """List saved reports from database (latest first)"""
    try:
        supabase = app.state.supabase
        if not supabase:
            return {"reports": [], "count": 0}

        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("reports")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"reports": response.data, "count": len(response.data)}
    except Exception as e:
        return {"error": str(e)}, 500


@app.get("/api/bulls-analysis")
async def get_bulls_analysis():
    """Get Bulls-focused analysis and recommendations"""
    try:
        supabase = app.state.supabase
        if not supabase:
            return {
                "team": "CHI",
                "generated_at": datetime.now().isoformat(),
                "next_game": None,
                "team_stats": None,
                "players": [],
                "risk_factors": [],
            }

        start_utc, end_utc = chicago_day_bounds_utc()
        games_resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("games")
            .select("id,home_team,away_team,commence_time")
            .gte("commence_time", start_utc.isoformat())
            .lt("commence_time", end_utc.isoformat())
            .order("commence_time")
            .execute()
        )
        games = games_resp.data or []

        bulls_game: dict | None = None
        for g in games:
            home = (g.get("home_team") or "").strip()
            away = (g.get("away_team") or "").strip()
            if home.lower() == "chicago bulls" or away.lower() == "chicago bulls":
                bulls_game = g
                break

        next_game: dict | None = None
        if bulls_game:
            gid = bulls_game.get("id")
            odds_resp = await anyio.to_thread.run_sync(
                lambda: supabase.table("odds")
                .select("bookmaker_key,bookmaker_title,market_type,team,outcome_name,point,price")
                .eq("game_id", gid)
                .execute()
            )
            odds_rows = odds_resp.data or []

            home_team = bulls_game.get("home_team")
            away_team = bulls_game.get("away_team")

            h2h_rows = [r for r in odds_rows if (r.get("market_type") == "h2h")]
            spreads_rows = [r for r in odds_rows if (r.get("market_type") == "spread")]
            totals_rows = [r for r in odds_rows if (r.get("market_type") == "totals")]

            home_best = _best_price_for_team(h2h_rows, str(home_team)) if home_team else None
            away_best = _best_price_for_team(h2h_rows, str(away_team)) if away_team else None

            # Derive a representative spread/total line (median across books)
            def _median_points(rows: list[dict], predicate) -> float | None:
                pts: list[float] = []
                for r in rows:
                    if not predicate(r):
                        continue
                    p = r.get("point")
                    try:
                        if p is None:
                            continue
                        pts.append(float(p))
                    except Exception:
                        continue
                if not pts:
                    return None
                return float(statistics.median(pts))

            spread_home = _median_points(
                spreads_rows,
                lambda r: (r.get("team") or "").strip().lower()
                == (str(home_team).strip().lower() if home_team else ""),
            )
            total_line = _median_points(totals_rows, lambda r: (r.get("outcome_name") or "").strip().lower() == "over")

            next_game = {
                "game_id": gid,
                "home_team": home_team,
                "away_team": away_team,
                "commence_time": bulls_game.get("commence_time"),
                "moneyline": {
                    "home": {"best_price": home_best[0], "best_book": home_best[1]} if home_best else None,
                    "away": {"best_price": away_best[0], "best_book": away_best[1]} if away_best else None,
                },
                "spread": {"home_line": spread_home},
                "total": {"line": total_line},
            }

        # Compute Bulls season stats & trends from player_game_stats if available.
        team_stats: dict | None = None
        top_players: list[dict] = []
        risk_factors: list[dict] = []
        bulls_betting: dict | None = None

        try:
            latest_resp = await anyio.to_thread.run_sync(
                lambda: supabase.table("player_game_stats")
                .select("season_year,game_date")
                .eq("team_tricode", "CHI")
                .order("game_date", desc=True)
                .limit(1)
                .execute()
            )
            latest_row = (latest_resp.data or [None])[0]
            season_year = latest_row.get("season_year") if isinstance(latest_row, dict) else None
            if season_year:
                chi_rows_resp = await anyio.to_thread.run_sync(
                    lambda: supabase.table("player_game_stats")
                    .select(
                        "game_id,game_date,matchup,team_tricode,player_id,player_name,position,minutes,points,rebounds_total,assists,"
                        "field_goals_made,field_goals_attempted,three_pointers_made,three_pointers_attempted,"
                        "free_throws_made,free_throws_attempted,rebounds_offensive,turnovers"
                    )
                    .eq("team_tricode", "CHI")
                    .eq("season_year", season_year)
                    .order("game_date", desc=True)
                    .range(0, 5000)
                    .execute()
                )
                chi_rows = chi_rows_resp.data or []
                game_ids: list[str] = []
                seen: set[str] = set()
                matchup_by_game: dict[str, str | None] = {}
                date_by_game: dict[str, str | None] = {}
                for r in chi_rows:
                    gid = r.get("game_id")
                    if not gid or gid in seen:
                        continue
                    seen.add(gid)
                    game_ids.append(gid)
                    matchup_by_game[gid] = r.get("matchup")
                    date_by_game[gid] = r.get("game_date")

                if game_ids:
                    all_rows_resp = await anyio.to_thread.run_sync(
                        lambda gids=game_ids: supabase.table("player_game_stats")
                        .select(
                            "game_id,team_tricode,minutes,points,field_goals_made,field_goals_attempted,three_pointers_made,three_pointers_attempted,"
                            "free_throws_made,free_throws_attempted,rebounds_offensive,turnovers"
                        )
                        .in_("game_id", gids)
                        .eq("season_year", season_year)
                        .range(0, 20000)
                        .execute()
                    )
                    all_rows = all_rows_resp.data or []

                    def _init_totals() -> dict:
                        return {
                            "points": 0.0,
                            "fgm": 0.0,
                            "fga": 0.0,
                            "tpm": 0.0,
                            "tpa": 0.0,
                            "ftm": 0.0,
                            "fta": 0.0,
                            "orb": 0.0,
                            "tov": 0.0,
                            "minutes": 0.0,
                        }

                    totals_by_game_team: dict[str, dict[str, dict]] = {}
                    for r in all_rows:
                        gid = r.get("game_id")
                        tcode = r.get("team_tricode")
                        if not gid or not tcode:
                            continue
                        g = totals_by_game_team.setdefault(gid, {})
                        tot = g.setdefault(tcode, _init_totals())
                        tot["points"] += float(r.get("points") or 0)
                        tot["fgm"] += float(r.get("field_goals_made") or 0)
                        tot["fga"] += float(r.get("field_goals_attempted") or 0)
                        tot["tpm"] += float(r.get("three_pointers_made") or 0)
                        tot["tpa"] += float(r.get("three_pointers_attempted") or 0)
                        tot["ftm"] += float(r.get("free_throws_made") or 0)
                        tot["fta"] += float(r.get("free_throws_attempted") or 0)
                        tot["orb"] += float(r.get("rebounds_offensive") or 0)
                        tot["tov"] += float(r.get("turnovers") or 0)
                        m = _parse_minutes_to_float(r.get("minutes"))
                        if m is not None:
                            tot["minutes"] += float(m)

                    # Build ordered game list (most recent first)
                    games_ordered: list[dict] = []
                    for gid in game_ids:
                        teams_totals = totals_by_game_team.get(gid) or {}
                        chi_totals = teams_totals.get("CHI")
                        if not chi_totals:
                            continue
                        opp_codes = [k for k in teams_totals.keys() if k != "CHI"]
                        opp_totals = teams_totals.get(opp_codes[0]) if opp_codes else None
                        games_ordered.append(
                            {
                                "game_id": gid,
                                "game_date": date_by_game.get(gid),
                                "matchup": matchup_by_game.get(gid),
                                "chi": chi_totals,
                                "opp": opp_totals,
                            }
                        )

                    wins = losses = 0
                    home_wins = home_losses = 0
                    away_wins = away_losses = 0
                    for g in games_ordered:
                        chi_pts = g["chi"]["points"]
                        opp_pts = (g["opp"] or {}).get("points")
                        if opp_pts is None:
                            continue
                        is_win = chi_pts > float(opp_pts)
                        if is_win:
                            wins += 1
                        else:
                            losses += 1

                        is_home = _matchup_is_home(g.get("matchup"))
                        if is_home is True:
                            if is_win:
                                home_wins += 1
                            else:
                                home_losses += 1
                        elif is_home is False:
                            if is_win:
                                away_wins += 1
                            else:
                                away_losses += 1

                    last5_games = games_ordered[:5]
                    last5_wins = last5_losses = 0
                    for g in last5_games:
                        chi_pts = g["chi"]["points"]
                        opp_pts = (g["opp"] or {}).get("points")
                        if opp_pts is None:
                            continue
                        if chi_pts > float(opp_pts):
                            last5_wins += 1
                        else:
                            last5_losses += 1

                    def _avg_metric(items: list[dict], extractor) -> float | None:
                        vals: list[float] = []
                        for x in items:
                            v = extractor(x)
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                                if not (fv != fv):
                                    vals.append(fv)
                            except Exception:
                                continue
                        if not vals:
                            return None
                        return float(statistics.mean(vals))

                    def _pct(made: float, att: float) -> float | None:
                        if att <= 0:
                            return None
                        return made / att

                    last7 = games_ordered[:7]
                    prev7 = games_ordered[7:14]

                    def _pace(g: dict) -> float | None:
                        chi = g["chi"]
                        opp = g.get("opp")
                        if not opp:
                            return None
                        chi_poss = _estimate_possessions(chi["fga"], chi["orb"], chi["tov"], chi["fta"])
                        opp_poss = _estimate_possessions(opp["fga"], opp["orb"], opp["tov"], opp["fta"])
                        if chi_poss is None or opp_poss is None:
                            return None
                        return (chi_poss + opp_poss) / 2.0

                    def _offrtg(g: dict) -> float | None:
                        chi = g["chi"]
                        poss = _estimate_possessions(chi["fga"], chi["orb"], chi["tov"], chi["fta"])
                        if poss is None or poss <= 0:
                            return None
                        return 100.0 * chi["points"] / poss

                    def _defrtg(g: dict) -> float | None:
                        chi = g["chi"]
                        opp = g.get("opp")
                        if not opp:
                            return None
                        poss = _estimate_possessions(chi["fga"], chi["orb"], chi["tov"], chi["fta"])
                        if poss is None or poss <= 0:
                            return None
                        return 100.0 * float(opp["points"]) / poss

                    def _three_pct(g: dict) -> float | None:
                        chi = g["chi"]
                        return _pct(chi["tpm"], chi["tpa"])

                    def _ft_pct(g: dict) -> float | None:
                        chi = g["chi"]
                        return _pct(chi["ftm"], chi["fta"])

                    last_pace = _avg_metric(last7, _pace)
                    prev_pace = _avg_metric(prev7, _pace)
                    last_off = _avg_metric(last7, _offrtg)
                    prev_off = _avg_metric(prev7, _offrtg)
                    last_def = _avg_metric(last7, _defrtg)
                    prev_def = _avg_metric(prev7, _defrtg)
                    last_3p = _avg_metric(last7, _three_pct)
                    prev_3p = _avg_metric(prev7, _three_pct)
                    last_ft = _avg_metric(last7, _ft_pct)
                    prev_ft = _avg_metric(prev7, _ft_pct)

                    def _delta(a: float | None, b: float | None) -> float | None:
                        if a is None or b is None:
                            return None
                        return a - b

                    d_pace = _delta(last_pace, prev_pace)
                    d_off = _delta(last_off, prev_off)
                    d_def = _delta(last_def, prev_def)
                    d_3p = _delta(last_3p, prev_3p)
                    d_ft = _delta(last_ft, prev_ft)

                    team_stats = {
                        "season_year": season_year,
                        "record": {"wins": wins, "losses": losses} if (wins + losses) > 0 else None,
                        "home_record": {"wins": home_wins, "losses": home_losses} if (home_wins + home_losses) > 0 else None,
                        "away_record": {"wins": away_wins, "losses": away_losses} if (away_wins + away_losses) > 0 else None,
                        "last5": {"wins": last5_wins, "losses": last5_losses} if (last5_wins + last5_losses) > 0 else None,
                        "ats": None,
                        "ou": None,
                        "trends": {
                            "pace": {
                                "value": last_pace,
                                "trend": _trend_direction(d_pace, 1.0),
                                "change": _format_delta(d_pace, is_pct=False),
                            },
                            "offRtg": {
                                "value": last_off,
                                "trend": _trend_direction(d_off, 1.0),
                                "change": _format_delta(d_off, is_pct=False),
                            },
                            "defRtg": {
                                "value": last_def,
                                "trend": _trend_direction(d_def, 1.0),
                                "change": _format_delta(d_def, is_pct=False),
                            },
                            "threePointPct": {
                                "value": last_3p,
                                "trend": _trend_direction(d_3p, 0.01),
                                "change": _format_delta(d_3p, is_pct=True),
                            },
                            "freeThrowPct": {
                                "value": last_ft,
                                "trend": _trend_direction(d_ft, 0.005),
                                "change": _format_delta(d_ft, is_pct=True),
                            },
                        },
                    }

                    # Top player averages over last 7 games (real data only)
                    last7_ids = {g["game_id"] for g in last7}
                    by_player: dict[int, dict] = {}
                    for r in chi_rows:
                        gid = r.get("game_id")
                        if not gid or gid not in last7_ids:
                            continue
                        pid = r.get("player_id")
                        if pid is None:
                            continue
                        try:
                            pid_int = int(pid)
                        except Exception:
                            continue
                        p = by_player.setdefault(
                            pid_int,
                            {
                                "player_id": pid_int,
                                "name": r.get("player_name"),
                                "position": r.get("position"),
                                "games": set(),
                                "points": 0.0,
                                "rebounds": 0.0,
                                "assists": 0.0,
                                "fgm": 0.0,
                                "fga": 0.0,
                                "ftm": 0.0,
                                "fta": 0.0,
                                "minutes": 0.0,
                            },
                        )
                        p["games"].add(gid)
                        p["points"] += float(r.get("points") or 0)
                        p["rebounds"] += float(r.get("rebounds_total") or 0)
                        p["assists"] += float(r.get("assists") or 0)
                        p["fgm"] += float(r.get("field_goals_made") or 0)
                        p["fga"] += float(r.get("field_goals_attempted") or 0)
                        p["ftm"] += float(r.get("free_throws_made") or 0)
                        p["fta"] += float(r.get("free_throws_attempted") or 0)
                        m = _parse_minutes_to_float(r.get("minutes"))
                        if m is not None:
                            p["minutes"] += float(m)

                    def _safe_div(n: float, d: float) -> float | None:
                        if d <= 0:
                            return None
                        return n / d

                    players_list: list[dict] = []
                    for p in by_player.values():
                        games_n = len(p["games"])
                        if games_n <= 0:
                            continue
                        players_list.append(
                            {
                                "name": p.get("name"),
                                "position": p.get("position"),
                                "role": p.get("position"),
                                "stats": {
                                    "ppg": p["points"] / games_n,
                                    "rpg": p["rebounds"] / games_n,
                                    "apg": p["assists"] / games_n,
                                    "fgPct": _safe_div(p["fgm"], p["fga"]),
                                    "ftPct": _safe_div(p["ftm"], p["fta"]),
                                },
                                "minutes": p["minutes"] / games_n if p["minutes"] > 0 else None,
                                "form": None,
                                "trend": None,
                            }
                        )

                    players_list.sort(key=lambda x: (x.get("minutes") or 0), reverse=True)
                    top_players = players_list[:8]

        except Exception as e:
            logger.warning(f"Bulls stats enrichment unavailable: {e}")

        try:
            bulls_betting = await _compute_betting_stats(supabase, "Chicago Bulls")
        except Exception as e:
            logger.warning(f"Bulls betting stats unavailable: {e}")

        if team_stats and bulls_betting:
            def _parse_record(record: str | None) -> tuple[int | None, int | None, int | None]:
                if not record:
                    return None, None, None
                parts = str(record).split("-")
                if len(parts) < 2:
                    return None, None, None
                try:
                    w = int(parts[0])
                    l = int(parts[1])
                    p = int(parts[2]) if len(parts) > 2 else 0
                    return w, l, p
                except Exception:
                    return None, None, None

            ats_w, ats_l, ats_p = _parse_record(bulls_betting.get("ats_record"))
            ou_w, ou_l, ou_p = _parse_record(bulls_betting.get("over_under"))
            team_stats["ats"] = {"covers": ats_w, "misses": ats_l, "pushes": ats_p}
            team_stats["ou"] = {"overs": ou_w, "unders": ou_l, "pushes": ou_p}

        # Risk factors (only if we can compute them from real dates)
        try:
            if next_game and next_game.get("commence_time"):
                ct = next_game.get("commence_time")
                next_dt = datetime.fromisoformat(str(ct).replace("Z", "+00:00"))
                next_chi_date = next_dt.astimezone(CHICAGO_TZ).date()

                last_date = None
                if team_stats and isinstance(team_stats, dict):
                    # We already queried latest game_date for CHI above
                    pass

                # Fetch last played game date for CHI (best-effort)
                last_resp = await anyio.to_thread.run_sync(
                    lambda: supabase.table("player_game_stats")
                    .select("game_date")
                    .eq("team_tricode", "CHI")
                    .order("game_date", desc=True)
                    .limit(1)
                    .execute()
                )
                last_row = (last_resp.data or [None])[0]
                if isinstance(last_row, dict) and last_row.get("game_date"):
                    try:
                        last_date = date.fromisoformat(str(last_row.get("game_date")))
                    except Exception:
                        last_date = None

                if last_date:
                    # If our last available box-score date is clearly stale compared to the
                    # scheduled next game date (e.g. historical dataset not updated),
                    # don't emit a potentially misleading back-to-back value.
                    days_diff = (next_chi_date - last_date).days
                    if 0 <= days_diff <= 10:
                        is_b2b = days_diff == 1
                        risk_factors.append(
                            {
                                "key": "back_to_back",
                                "value": bool(is_b2b),
                                "meta": {
                                    "previous_game_date": last_date.isoformat(),
                                    "next_game_date": next_chi_date.isoformat(),
                                },
                            }
                        )

                home_team = (next_game.get("home_team") or "").strip().lower()
                bulls_home = home_team == "chicago bulls"
                if bulls_home and team_stats and isinstance(team_stats, dict):
                    hr = team_stats.get("home_record")
                    record_str = None
                    if isinstance(hr, dict) and isinstance(hr.get("wins"), int) and isinstance(hr.get("losses"), int):
                        record_str = f"{hr['wins']}-{hr['losses']}"
                    risk_factors.append(
                        {
                            "key": "home_court",
                            "value": True,
                            "meta": {"home_record": record_str},
                        }
                    )
        except Exception as e:
            logger.warning(f"Risk factor computation skipped: {e}")

        return {
            "team": "CHI",
            "generated_at": datetime.now().isoformat(),
            "next_game": next_game,
            "team_stats": team_stats,
            "players": top_players,
            "risk_factors": risk_factors,
        }
    except Exception as e:
        logger.error(f"Error generating Bulls analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Bulls analysis")


@app.post("/api/scrape/bulls-players")
async def scrape_bulls_players_endpoint():
    """Manually trigger Bulls players scraping with anti-bot protection"""
    try:
        from scrapers import get_bulls_players_data, save_bulls_players
        
        logger.info("Manual Bulls players scraping triggered")
        supabase = app.state.supabase
        
        # Scrape Bulls players using advanced anti-bot protection
        players = await get_bulls_players_data()
        
        if players:
            await save_bulls_players(supabase, players)
            logger.info(f"Successfully scraped and saved {len(players)} Bulls players")
            return {
                "success": True,
                "message": f"Successfully scraped {len(players)} Bulls players",
                "players_count": len(players),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.warning("No Bulls players scraped")
            return {
                "success": False,
                "message": "No Bulls players found or scraping failed",
                "players_count": 0,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error scraping Bulls players: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scrape Bulls players: {str(e)}")


@app.get("/api/betting-recommendations")
async def get_betting_recommendations():
    """Get current betting recommendations"""
    try:
        supabase = app.state.supabase
        if not supabase:
            return {"generated_at": datetime.now().isoformat(), "picks": [], "count": 0}

        start_utc, end_utc = chicago_day_bounds_utc()

        games_resp = await anyio.to_thread.run_sync(
            lambda: supabase.table("games")
            .select("id,home_team,away_team,commence_time")
            .gte("commence_time", start_utc.isoformat())
            .lt("commence_time", end_utc.isoformat())
            .execute()
        )
        games = games_resp.data or []
        if not games:
            return {"generated_at": datetime.now().isoformat(), "picks": [], "count": 0}

        candidates: list[dict] = []

        for game in games:
            game_id = game.get("id")
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            commence_time = game.get("commence_time")
            if not game_id or not home_team or not away_team:
                continue

            odds_resp = await anyio.to_thread.run_sync(
                lambda gid=game_id: supabase.table("odds")
                .select("bookmaker_key,bookmaker_title,market_type,team,price")
                .eq("game_id", gid)
                .eq("market_type", "h2h")
                .execute()
            )
            h2h_rows = odds_resp.data or []
            if not h2h_rows:
                continue

            consensus = _compute_no_vig_consensus_probs(h2h_rows, home_team, away_team)
            if not consensus:
                continue
            p_home, p_away = consensus

            home_best = _best_price_for_team(h2h_rows, home_team)
            away_best = _best_price_for_team(h2h_rows, away_team)
            if not home_best or not away_best:
                continue

            home_price, home_book = home_best
            away_price, away_book = away_best

            candidates.append(
                {
                    "market": "h2h",
                    "team": home_team,
                    "opponent": away_team,
                    "game_id": game_id,
                    "commence_time": commence_time,
                    "best_price": home_price,
                    "best_book": home_book,
                    "consensus_prob": p_home,
                    "edge": p_home * home_price - 1.0,
                }
            )
            candidates.append(
                {
                    "market": "h2h",
                    "team": away_team,
                    "opponent": home_team,
                    "game_id": game_id,
                    "commence_time": commence_time,
                    "best_price": away_price,
                    "best_book": away_book,
                    "consensus_prob": p_away,
                    "edge": p_away * away_price - 1.0,
                }
            )

        positives = [c for c in candidates if (c.get("edge") or 0) > 0]
        ranked = sorted((positives or candidates), key=lambda x: x.get("edge") or -999, reverse=True)
        ranked = ranked[:20]

        return {"generated_at": datetime.now().isoformat(), "picks": ranked, "count": len(ranked)}
    except Exception as e:
        logger.error(f"Error generating betting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate betting recommendations")


@app.get("/api/arbitrage-opportunities")
async def get_arbitrage_opportunities():
    """Find arbitrage betting opportunities"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        # Mock odds data - replace with real API integration
        odds_data = []
        opportunities = await generator.identify_arbitrage_opportunities(odds_data)
        return {"opportunities": opportunities, "count": len(opportunities)}
    except Exception as e:
        logger.error(f"Error finding arbitrage opportunities: {e}")
        raise HTTPException(status_code=500, detail="Failed to find arbitrage opportunities")


@app.post("/api/betting-slip")
async def generate_betting_slip(bets: List[dict], total_stake: float = 100):
    """Generate professional betting slip with Kelly criterion sizing"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        formatted_slip = generator.format_betting_slip(bets, total_stake)
        return formatted_slip
    except Exception as e:
        logger.error(f"Error generating betting slip: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate betting slip")


@app.get("/api/kelly-calculator")
async def calculate_kelly(estimated_prob: float, decimal_odds: float):
    """Calculate Kelly Criterion bet sizing"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        kelly_fraction = generator.calculate_kelly_criterion(estimated_prob, decimal_odds)
        return {
            "kelly_fraction": kelly_fraction,
            "percentage": kelly_fraction * 100,
            "recommended_stake": f"{kelly_fraction * 100:.2f}% of bankroll"
        }
    except Exception as e:
        logger.error(f"Error calculating Kelly criterion: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate Kelly criterion")


@app.get("/api/performance-metrics")
async def get_performance_metrics():
    """Get betting performance and ROI metrics"""
    try:
        supabase = app.state.supabase
        generator = NBAReportGenerator(supabase)
        # Mock bet history - replace with real database
        bet_history = []
        metrics = generator.calculate_roi_projection(bet_history)
        return metrics
    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate performance metrics")


@app.get("/api/teams/analysis")
async def get_teams_analysis(include_betting: bool = False, max_games: int | None = None):
    """Get comprehensive analysis for all NBA teams"""
    try:
        supabase = app.state.supabase
        if not supabase:
            return {"teams": [], "count": 0, "conferences": {"Eastern": [], "Western": []}}

        env_max_games = int(os.getenv("TEAMS_ANALYSIS_MAX_GAMES", "20"))
        effective_max_games = max(5, min(82, max_games if max_games is not None else env_max_games))

        # Get all teams with basic info
        teams_response = await anyio.to_thread.run_sync(
            lambda: supabase.table("teams").select("*").order("abbreviation").execute()
        )
        
        teams_analysis: list[dict] = []

        conferences = {
            'Eastern': ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DET', 'IND', 'MIA', 'MIL', 'NYK', 'ORL', 'PHI', 'TOR', 'WAS'],
            'Western': ['DAL', 'DEN', 'GSW', 'HOU', 'LAC', 'LAL', 'MEM', 'MIN', 'NOP', 'OKC', 'PHX', 'POR', 'SAC', 'SAS', 'UTA']
        }
        
        divisions = {
            'Atlantic': ['BOS', 'BKN', 'NYK', 'PHI', 'TOR'],
            'Central': ['CHI', 'CLE', 'DET', 'IND', 'MIL'],
            'Southeast': ['ATL', 'CHA', 'MIA', 'ORL', 'WAS'],
            'Northwest': ['DEN', 'MIN', 'OKC', 'POR', 'UTA'],
            'Pacific': ['GSW', 'LAC', 'LAL', 'PHX', 'SAC'],
            'Southwest': ['DAL', 'HOU', 'MEM', 'NOP', 'SAS']
        }
        
        # Pull a lightweight real list of players to populate "key_players" without fabricating.
        players_by_team: dict[str, list[str]] = {}
        try:
            players_resp = await anyio.to_thread.run_sync(
                lambda: supabase.table("players")
                .select("name,team_abbreviation,jersey_number")
                .eq("is_active", True)
                .execute()
            )
            for p in (players_resp.data or []):
                abbr = (p.get("team_abbreviation") or "").strip().upper()
                name = (p.get("name") or "").strip()
                if not abbr or not name:
                    continue
                players_by_team.setdefault(abbr, []).append(name)
        except Exception as e:
            logger.warning(f"Unable to load players for key_players: {e}")

        cache_map = {}
        if include_betting:
            try:
                cache_map = await _load_betting_cache_map(supabase)
            except Exception as e:
                logger.warning(f"Betting cache unavailable: {e}")

        for team in teams_response.data or []:
            abbr = (team.get('abbreviation') or '').strip().upper()
            try:
                games_ordered, _season_year = await _load_team_games_from_stats(
                    supabase, abbr, max_games=effective_max_games
                )
            except Exception as e:
                logger.warning(f"Skipping team stats for {abbr}: {e}")
                games_ordered = []
            summary = _summarize_team_games(abbr, games_ordered)
            betting_stats = None
            if include_betting:
                cached = cache_map.get(team.get("full_name") or "")
                if cached and not _betting_cache_expired(cached.get("computed_at"), int(os.getenv("BETTING_CACHE_TTL_HOURS", "6"))):
                    betting_stats = {
                        "ats_record": cached.get("ats_record"),
                        "ats_percentage": cached.get("ats_percentage"),
                        "over_under": cached.get("over_under"),
                        "ou_percentage": cached.get("ou_percentage"),
                        "avg_total": cached.get("avg_total"),
                        "games_count": cached.get("games_count"),
                    }

            # Determine conference and division from static NBA mapping (not fabricated stats).
            conference = 'Eastern' if abbr in conferences['Eastern'] else 'Western'
            division = next((div for div, teams in divisions.items() if abbr in teams), 'Unknown')

            team_analysis = {
                **team,
                'conference': conference,
                'division': division,
                'season_stats': summary.get("season_stats"),
                'recent_form': summary.get("recent_form"),
                'betting_stats': betting_stats,
                'key_players': (players_by_team.get(abbr) or [])[:3],
                'strength_rating': summary.get("strength_rating"),
                'last_updated': datetime.now().isoformat(),
            }
            teams_analysis.append(team_analysis)
        
        return {
            'teams': teams_analysis,
            'count': len(teams_analysis),
            'conferences': {
                'Eastern': [t for t in teams_analysis if t.get('conference') == 'Eastern'],
                'Western': [t for t in teams_analysis if t.get('conference') == 'Western'],
            },
        }
        
    except Exception as e:
        logger.error(f"Error fetching teams analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch teams analysis")


@app.get("/api/teams/{team_abbrev}/analysis")
async def get_team_analysis(team_abbrev: str):
    """Get detailed analysis for a specific team"""
    try:
        supabase = app.state.supabase
        team_abbrev = team_abbrev.upper()
        
        # Get team basic info
        team_response = await anyio.to_thread.run_sync(
            lambda: supabase.table("teams")
            .select("*")
            .eq("abbreviation", team_abbrev)
            .single()
            .execute()
        )
        
        if not team_response.data:
            raise HTTPException(status_code=404, detail=f"Team '{team_abbrev}' not found")
        
        team = team_response.data
        
        games_ordered, season_year = await _load_team_games_from_stats(supabase, team_abbrev, max_games=82)
        summary = _summarize_team_games(team_abbrev, games_ordered)

        recent_games: list[dict] = []
        for g in games_ordered[:5]:
            opp_pts = (g.get("opp") or {}).get("points")
            if opp_pts is None:
                continue
            team_pts = g["team"]["points"]
            recent_games.append(
                {
                    "date": g.get("game_date"),
                    "opponent": _opponent_from_matchup(team_abbrev, g.get("matchup")),
                    "home": _matchup_is_home(g.get("matchup")),
                    "team_score": team_pts,
                    "opponent_score": opp_pts,
                    "result": "W" if float(team_pts) > float(opp_pts) else "L",
                    "margin": abs(float(team_pts) - float(opp_pts)),
                }
            )

        betting_stats = await _compute_betting_stats(supabase, team.get("full_name") or "")
        analysis = {
            **team,
            "season_year": season_year,
            "season_stats": summary.get("season_stats"),
            "recent_form": summary.get("recent_form"),
            "betting_stats": betting_stats,
            "strength_rating": summary.get("strength_rating"),
            "recent_games": recent_games,
            "last_updated": datetime.now().isoformat(),
        }

        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team analysis for {team_abbrev}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch team analysis")


# ============================================
# ADVANCED ANALYTICS ENDPOINTS
# ============================================

@app.get("/api/analytics/prop-bet")
async def analyze_prop_bet(
    player_name: str,
    stat_type: str,  # 'points', 'rebounds_total', 'assists'
    line: float,
    games: int = 20,
    opponent: str = None
):
    """
    Analyze prop bet value based on historical data
    
    Example: /api/analytics/prop-bet?player_name=Zach LaVine&stat_type=points&line=24.5&games=20&opponent=LAL
    """
    try:
        from analytics import PropBetPredictor
        
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        predictor = PropBetPredictor(supabase)
        result = await predictor.analyze_prop(player_name, stat_type, line, games, opponent)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing prop bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/matchup/team")
async def analyze_team_matchup(
    team: str,  # e.g., 'CHI'
    opponent: str,  # e.g., 'LAL'
    seasons_back: int = 3
):
    """
    Analyze team vs team matchup history
    
    Example: /api/analytics/matchup/team?team=CHI&opponent=LAL&seasons_back=3
    """
    try:
        from analytics import MatchupAnalyzer
        
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        analyzer = MatchupAnalyzer(supabase)
        result = await analyzer.analyze_team_matchup(team.upper(), opponent.upper(), seasons_back)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing team matchup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/matchup/player")
async def analyze_player_matchup(
    player_name: str,
    opponent: str,
    seasons_back: int = 3
):
    """
    Analyze player performance vs specific opponent
    
    Example: /api/analytics/matchup/player?player_name=Zach LaVine&opponent=LAL&seasons_back=3
    """
    try:
        from analytics import MatchupAnalyzer
        
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        analyzer = MatchupAnalyzer(supabase)
        result = await analyzer.analyze_player_vs_opponent(player_name, opponent.upper(), seasons_back)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing player matchup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/form")
async def get_player_form(
    player_name: str,
    games: int = 15
):
    """
    Get player form tracker with trends and rolling averages
    
    Example: /api/analytics/form?player_name=Zach LaVine&games=15
    """
    try:
        from analytics import FormTracker
        
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        tracker = FormTracker(supabase)
        result = await tracker.get_player_form(player_name, games)
        
        return result
        
    except Exception as e:
        logger.error(f"Error tracking player form: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/injury-impact")
async def analyze_injury_impact(
    team: str,  # e.g., 'CHI'
    missing_player: str,  # e.g., 'Zach LaVine'
    seasons_back: int = 2
):
    """
    Analyze impact of player absence on team and other players
    
    Example: /api/analytics/injury-impact?team=CHI&missing_player=Zach LaVine&seasons_back=2
    """
    try:
        from analytics import InjuryImpactAnalyzer
        
        supabase = app.state.supabase
        if not supabase:
            raise HTTPException(status_code=503, detail="Database not available")
        
        analyzer = InjuryImpactAnalyzer(supabase)
        result = await analyzer.analyze_player_absence_impact(team.upper(), missing_player, seasons_back)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing injury impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "nba-analytics-backend",
        "version": "1.0.0"
    }
