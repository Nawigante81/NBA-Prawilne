"""
NBA Betting Analytics Backend - Stats Service
Handles fetching and storing NBA statistics from nba_api
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta, timezone

from nba_api.stats.endpoints import (
    leaguegamefinder,
    boxscoretraditionalv2,
    boxscoreadvancedv2,
)
from nba_api.stats.static import teams as nba_teams

import settings import NBA_API_CACHE_TTL_SECONDS, NBA_STATS_WINDOW
from db import fetch_all, execute_query, get_cache, set_cache, fetch_one

logger = logging.getLogger(__name__)

# NBA team abbreviation mapping (nba_api uses different abbreviations)
NBA_TEAM_MAPPING = {
    "ATL": "ATL", "BOS": "BOS", "BKN": "BKN", "CHA": "CHA", "CHI": "CHI",
    "CLE": "CLE", "DAL": "DAL", "DEN": "DEN", "DET": "DET", "GSW": "GSW",
    "HOU": "HOU", "IND": "IND", "LAC": "LAC", "LAL": "LAL", "MEM": "MEM",
    "MIA": "MIA", "MIL": "MIL", "MIN": "MIN", "NOP": "NOP", "NYK": "NYK",
    "OKC": "OKC", "ORL": "ORL", "PHI": "PHI", "PHX": "PHX", "POR": "POR",
    "SAC": "SAC", "SAS": "SAS", "TOR": "TOR", "UTA": "UTA", "WAS": "WAS",
}

# Rate limiting for NBA API (max 20 requests per 60 seconds)
NBA_API_RATE_LIMIT_DELAY = 3.5  # seconds between requests


async def rate_limit_delay():
    """Apply rate limiting delay for NBA API"""
    await asyncio.sleep(NBA_API_RATE_LIMIT_DELAY)


def get_nba_team_id(team_abbrev: str) -> Optional[int]:
    """Get NBA team ID from abbreviation"""
    all_teams = nba_teams.get_teams()
    for team in all_teams:
        if team["abbreviation"] == team_abbrev:
            return team["id"]
    return None


def normalize_team_abbrev(nba_abbrev: str) -> str:
    """Normalize team abbreviation from nba_api to our format"""
    return NBA_TEAM_MAPPING.get(nba_abbrev, nba_abbrev)


async def sync_nba_teams() -> Dict[str, Any]:
    """
    Fetch and update teams table with conference and division info
    
    Returns:
        Dict with status and counts
    """
    try:
        logger.info("Starting NBA teams sync...")
        
        # Check cache first
        cache_key = "nba_teams_all"
        cached = await get_cache("nba_api", cache_key)
        
        if cached:
            teams_data = cached
            logger.info("Using cached NBA teams data")
        else:
            # Fetch from nba_api (runs synchronously)
            def fetch_teams():
                return nba_teams.get_teams()
            
            teams_data = await asyncio.to_thread(fetch_teams)
            
            # Cache the result
            await set_cache("nba_api", cache_key, teams_data, NBA_API_CACHE_TTL_SECONDS)
            logger.info(f"Fetched {len(teams_data)} teams from NBA API")
        
        # Update teams in database
        updated = 0
        for team in teams_data:
            abbrev = normalize_team_abbrev(team["abbreviation"])
            
            # Determine conference and division from team info
            # NBA API doesn't directly provide this, so we use a mapping
            conference, division = get_conference_division(abbrev)
            
            query = """
                INSERT INTO teams (abbrev, full_name, city, conference, division)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (abbrev)
                DO UPDATE SET
                    full_name = EXCLUDED.full_name,
                    city = EXCLUDED.city,
                    conference = EXCLUDED.conference,
                    division = EXCLUDED.division
            """
            
            await execute_query(
                query,
                abbrev,
                team["full_name"],
                team["city"],
                conference,
                division
            )
            updated += 1
        
        logger.info(f"Successfully synced {updated} teams")
        
        return {
            "status": "success",
            "teams_synced": updated
        }
        
    except Exception as e:
        logger.error(f"Error syncing NBA teams: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


def get_conference_division(abbrev: str) -> Tuple[str, str]:
    """Get conference and division for a team"""
    # Eastern Conference
    atlantic = ["BOS", "BKN", "NYK", "PHI", "TOR"]
    central = ["CHI", "CLE", "DET", "IND", "MIL"]
    southeast = ["ATL", "CHA", "MIA", "ORL", "WAS"]
    
    # Western Conference
    northwest = ["DEN", "MIN", "OKC", "POR", "UTA"]
    pacific = ["GSW", "LAC", "LAL", "PHX", "SAC"]
    southwest = ["DAL", "HOU", "MEM", "NOP", "SAS"]
    
    if abbrev in atlantic:
        return "Eastern", "Atlantic"
    elif abbrev in central:
        return "Eastern", "Central"
    elif abbrev in southeast:
        return "Eastern", "Southeast"
    elif abbrev in northwest:
        return "Western", "Northwest"
    elif abbrev in pacific:
        return "Western", "Pacific"
    elif abbrev in southwest:
        return "Western", "Southwest"
    else:
        return "Unknown", "Unknown"


async def sync_nba_games(days_ahead: int = 7, days_back: int = 3) -> Dict[str, Any]:
    """
    Fetch recent and upcoming games and store in games table
    
    Args:
        days_ahead: Number of days ahead to fetch
        days_back: Number of days back to fetch
        
    Returns:
        Dict with status and counts
    """
    try:
        logger.info(f"Starting NBA games sync (back: {days_back}, ahead: {days_ahead})...")
        
        # Build cache key with date range
        today = datetime.now(timezone.utc).date()
        cache_key = f"nba_games_{(today - timedelta(days=days_back)).isoformat()}_{(today + timedelta(days=days_ahead)).isoformat()}"
        
        cached = await get_cache("nba_api", cache_key)
        
        if cached:
            games_data = cached
            logger.info("Using cached NBA games data")
        else:
            # Calculate date range
            date_from = (today - timedelta(days=days_back)).strftime("%m/%d/%Y")
            date_to = (today + timedelta(days=days_ahead)).strftime("%m/%d/%Y")
            
            # Fetch games using leaguegamefinder
            def fetch_games():
                finder = leaguegamefinder.LeagueGameFinder(
                    date_from_nullable=date_from,
                    date_to_nullable=date_to,
                    league_id_nullable="00"  # NBA
                )
                return finder.get_data_frames()[0].to_dict('records')
            
            games_data = await asyncio.to_thread(fetch_games)
            
            # Cache the result
            await set_cache("nba_api", cache_key, games_data, NBA_API_CACHE_TTL_SECONDS)
            logger.info(f"Fetched {len(games_data)} game records from NBA API")
            
            # Rate limit
            await rate_limit_delay()
        
        # Process and deduplicate games (each game appears twice, once per team)
        games_by_id = {}
        for record in games_data:
            game_id = str(record.get("GAME_ID"))
            if game_id not in games_by_id:
                # Parse game date
                game_date_str = record.get("GAME_DATE")
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except:
                    game_date = datetime.now(timezone.utc)
                
                # Determine home/away teams from matchup string (e.g., "ATL @ BOS")
                matchup = record.get("MATCHUP", "")
                team_abbrev = normalize_team_abbrev(record.get("TEAM_ABBREVIATION", ""))
                
                if "@" in matchup:
                    # Away team
                    away_team = team_abbrev
                    home_team = normalize_team_abbrev(matchup.split("@")[1].strip())
                else:
                    # Home team (vs.)
                    home_team = team_abbrev
                    away_team = normalize_team_abbrev(matchup.split("vs.")[1].strip())
                
                games_by_id[game_id] = {
                    "nba_game_id": game_id,
                    "home_team": home_team,
                    "away_team": away_team,
                    "commence_time": game_date,
                    "wl": record.get("WL")  # Win/Loss indicator
                }
        
        # Insert/update games in database
        inserted = 0
        updated = 0
        
        for game_id, game_data in games_by_id.items():
            # Generate our game ID format
            game_date_str = game_data["commence_time"].strftime("%Y%m%d")
            our_game_id = f"{game_date_str}_{game_data['away_team']}_{game_data['home_team']}"
            
            # Determine status based on WL field
            status = "final" if game_data.get("wl") else "scheduled"
            
            # Check if game exists
            check_query = "SELECT id FROM games WHERE nba_game_id = $1"
            existing = await fetch_one(check_query, game_data["nba_game_id"])
            
            if existing:
                # Update existing game
                query = """
                    UPDATE games
                    SET status = $1, commence_time = $2
                    WHERE nba_game_id = $3
                """
                await execute_query(query, status, game_data["commence_time"], game_data["nba_game_id"])
                updated += 1
            else:
                # Insert new game
                query = """
                    INSERT INTO games (id, home_team, away_team, commence_time, nba_game_id, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO NOTHING
                """
                await execute_query(
                    query,
                    our_game_id,
                    game_data["home_team"],
                    game_data["away_team"],
                    game_data["commence_time"],
                    game_data["nba_game_id"],
                    status
                )
                inserted += 1
        
        logger.info(f"Games sync complete: {inserted} inserted, {updated} updated")
        
        return {
            "status": "success",
            "games_inserted": inserted,
            "games_updated": updated
        }
        
    except Exception as e:
        logger.error(f"Error syncing NBA games: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def sync_game_results() -> Dict[str, Any]:
    """
    Fetch box scores for finished games and store in team_game_results
    
    Returns:
        Dict with status and counts
    """
    try:
        logger.info("Starting game results sync...")
        
        # Get finished games without results
        query = """
            SELECT g.id, g.nba_game_id, g.home_team, g.away_team
            FROM games g
            WHERE g.status = 'final'
            AND g.nba_game_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM team_game_results tgr
                WHERE tgr.game_id = g.id
            )
            LIMIT 20
        """
        
        games_to_process = await fetch_all(query)
        logger.info(f"Found {len(games_to_process)} games to process")
        
        processed = 0
        
        for game in games_to_process:
            try:
                nba_game_id = game["nba_game_id"]
                cache_key = f"box_score_{nba_game_id}"
                
                cached = await get_cache("nba_api", cache_key)
                
                if cached:
                    box_score_data = cached
                else:
                    # Fetch box score
                    def fetch_box_score():
                        box_score = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=nba_game_id)
                        return box_score.get_normalized_dict()
                    
                    box_score_data = await asyncio.to_thread(fetch_box_score)
                    await set_cache("nba_api", cache_key, box_score_data, NBA_API_CACHE_TTL_SECONDS * 24)  # Cache for 24 hours
                    await rate_limit_delay()
                
                # Extract team scores from LineScore
                line_score = box_score_data.get("LineScore", [])
                
                for team_score in line_score:
                    team_abbrev = normalize_team_abbrev(team_score.get("TEAM_ABBREVIATION", ""))
                    pts = team_score.get("PTS", 0)
                    
                    # Determine if home team
                    is_home = team_abbrev == game["home_team"]
                    
                    # Calculate points against
                    opponent_score = next(
                        (t.get("PTS", 0) for t in line_score if normalize_team_abbrev(t.get("TEAM_ABBREVIATION", "")) != team_abbrev),
                        0
                    )
                    
                    # Insert result
                    insert_query = """
                        INSERT INTO team_game_results (game_id, team_abbrev, points_for, points_against, is_home)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (game_id, team_abbrev) DO NOTHING
                    """
                    
                    await execute_query(
                        insert_query,
                        game["id"],
                        team_abbrev,
                        pts,
                        opponent_score,
                        is_home
                    )
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing game {game.get('nba_game_id')}: {e}")
                continue
        
        logger.info(f"Game results sync complete: {processed} games processed")
        
        return {
            "status": "success",
            "games_processed": processed
        }
        
    except Exception as e:
        logger.error(f"Error syncing game results: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def sync_team_stats() -> Dict[str, Any]:
    """
    Fetch and store team game stats (pace, off_rtg, def_rtg, 3pt%, FT%)
    
    Returns:
        Dict with status and counts
    """
    try:
        logger.info("Starting team stats sync...")
        
        # Get finished games without team stats
        query = """
            SELECT g.id, g.nba_game_id, g.home_team, g.away_team
            FROM games g
            WHERE g.status = 'final'
            AND g.nba_game_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM team_game_stats tgs
                WHERE tgs.game_id = g.id
            )
            LIMIT 20
        """
        
        games_to_process = await fetch_all(query)
        logger.info(f"Found {len(games_to_process)} games to process for team stats")
        
        processed = 0
        
        for game in games_to_process:
            try:
                nba_game_id = game["nba_game_id"]
                cache_key = f"box_score_advanced_{nba_game_id}"
                
                cached = await get_cache("nba_api", cache_key)
                
                if cached:
                    advanced_data = cached
                else:
                    # Fetch advanced box score
                    def fetch_advanced():
                        box_score = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=nba_game_id)
                        return box_score.get_normalized_dict()
                    
                    advanced_data = await asyncio.to_thread(fetch_advanced)
                    await set_cache("nba_api", cache_key, advanced_data, NBA_API_CACHE_TTL_SECONDS * 24)
                    await rate_limit_delay()
                
                # Extract team stats
                team_stats = advanced_data.get("TeamStats", [])
                
                for team_stat in team_stats:
                    team_abbrev = normalize_team_abbrev(team_stat.get("TEAM_ABBREVIATION", ""))
                    
                    # Extract stats
                    pace = team_stat.get("PACE")
                    off_rtg = team_stat.get("OFF_RATING")
                    def_rtg = team_stat.get("DEF_RATING")
                    
                    # Get traditional stats for shooting percentages
                    # We need to fetch traditional box score too
                    trad_cache_key = f"box_score_{nba_game_id}"
                    trad_cached = await get_cache("nba_api", trad_cache_key)
                    
                    three_pt_pct = None
                    ft_pct = None
                    
                    if trad_cached:
                        team_stats_trad = trad_cached.get("TeamStats", [])
                        for ts in team_stats_trad:
                            if normalize_team_abbrev(ts.get("TEAM_ABBREVIATION", "")) == team_abbrev:
                                three_pt_pct = ts.get("FG3_PCT")
                                ft_pct = ts.get("FT_PCT")
                                break
                    
                    # Insert stats
                    insert_query = """
                        INSERT INTO team_game_stats (game_id, team_abbrev, pace, off_rtg, def_rtg, three_pt_pct, ft_pct)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (game_id, team_abbrev) DO NOTHING
                    """
                    
                    await execute_query(
                        insert_query,
                        game["id"],
                        team_abbrev,
                        pace,
                        off_rtg,
                        def_rtg,
                        three_pt_pct,
                        ft_pct
                    )
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing team stats for game {game.get('nba_game_id')}: {e}")
                continue
        
        logger.info(f"Team stats sync complete: {processed} games processed")
        
        return {
            "status": "success",
            "games_processed": processed
        }
        
    except Exception as e:
        logger.error(f"Error syncing team stats: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def sync_player_stats() -> Dict[str, Any]:
    """
    Fetch and store player game stats (minutes, pts, reb, ast, usage)
    
    Returns:
        Dict with status and counts
    """
    try:
        logger.info("Starting player stats sync...")
        
        # Get finished games without player stats
        query = """
            SELECT g.id, g.nba_game_id
            FROM games g
            WHERE g.status = 'final'
            AND g.nba_game_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM player_game_stats pgs
                WHERE pgs.game_id = g.id
            )
            LIMIT 10
        """
        
        games_to_process = await fetch_all(query)
        logger.info(f"Found {len(games_to_process)} games to process for player stats")
        
        processed = 0
        
        for game in games_to_process:
            try:
                nba_game_id = game["nba_game_id"]
                cache_key = f"player_stats_{nba_game_id}"
                
                cached = await get_cache("nba_api", cache_key)
                
                if cached:
                    box_score_data = cached
                    advanced_data = cached.get("advanced")
                else:
                    # Fetch both traditional and advanced box scores
                    def fetch_both():
                        traditional = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=nba_game_id)
                        advanced = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=nba_game_id)
                        return {
                            "traditional": traditional.get_normalized_dict(),
                            "advanced": advanced.get_normalized_dict()
                        }
                    
                    box_score_data = await asyncio.to_thread(fetch_both)
                    await set_cache("nba_api", cache_key, box_score_data, NBA_API_CACHE_TTL_SECONDS * 24)
                    await rate_limit_delay()
                    advanced_data = box_score_data.get("advanced")
                    box_score_data = box_score_data.get("traditional")
                
                # Get player stats from traditional box score
                player_stats_trad = box_score_data.get("PlayerStats", [])
                player_stats_adv = advanced_data.get("PlayerStats", []) if advanced_data else []
                
                # Create usage lookup
                usage_lookup = {}
                for ps in player_stats_adv:
                    player_id = ps.get("PLAYER_ID")
                    usage_lookup[player_id] = ps.get("USG_PCT")
                
                for player_stat in player_stats_trad:
                    nba_player_id = player_stat.get("PLAYER_ID")
                    player_name = player_stat.get("PLAYER_NAME", "")
                    team_abbrev = normalize_team_abbrev(player_stat.get("TEAM_ABBREVIATION", ""))
                    
                    # Skip if no minutes played
                    minutes = player_stat.get("MIN")
                    if not minutes or minutes == "0:00":
                        continue
                    
                    # Convert minutes to decimal
                    try:
                        if ":" in str(minutes):
                            mins, secs = str(minutes).split(":")
                            minutes_decimal = int(mins) + int(secs) / 60.0
                        else:
                            minutes_decimal = float(minutes)
                    except:
                        continue
                    
                    # Get or create player
                    player_query = """
                        INSERT INTO players (nba_player_id, team_abbrev, name)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (nba_player_id)
                        DO UPDATE SET team_abbrev = EXCLUDED.team_abbrev
                        RETURNING id
                    """
                    
                    player_result = await fetch_one(player_query, nba_player_id, team_abbrev, player_name)
                    player_id = player_result["id"]
                    
                    # Extract stats
                    pts = player_stat.get("PTS", 0)
                    reb = player_stat.get("REB", 0)
                    ast = player_stat.get("AST", 0)
                    usage = usage_lookup.get(nba_player_id)
                    
                    # Insert player stats
                    insert_query = """
                        INSERT INTO player_game_stats (game_id, player_id, team_abbrev, minutes, pts, reb, ast, usage)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (game_id, player_id) DO NOTHING
                    """
                    
                    await execute_query(
                        insert_query,
                        game["id"],
                        player_id,
                        team_abbrev,
                        minutes_decimal,
                        pts,
                        reb,
                        ast,
                        usage
                    )
                
                processed += 1
                
            except Exception as e:
                logger.error(f"Error processing player stats for game {game.get('nba_game_id')}: {e}")
                continue
        
        logger.info(f"Player stats sync complete: {processed} games processed")
        
        return {
            "status": "success",
            "games_processed": processed
        }
        
    except Exception as e:
        logger.error(f"Error syncing player stats: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


async def sync_all_nba_stats() -> Dict[str, Any]:
    """
    Run all sync functions in sequence
    
    Returns:
        Dict with combined results
    """
    logger.info("Starting full NBA stats sync...")
    
    results = {
        "teams": await sync_nba_teams(),
        "games": await sync_nba_games(),
        "game_results": await sync_game_results(),
        "team_stats": await sync_team_stats(),
        "player_stats": await sync_player_stats(),
    }
    
    logger.info("Full NBA stats sync complete")
    
    return {
        "status": "success",
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
