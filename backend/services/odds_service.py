"""
NBA Betting Analytics Backend - Odds Service
Handles fetching, storing, and analyzing odds data from The Odds API
"""
import logging
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date, timezone
import statistics

import settings import (
    ODDS_API_KEY,
    ODDS_MAX_CALLS_PER_DAY,
    ODDS_BOOKMAKERS_ALLOWLIST,
    ODDS_SPORT_KEY,
    ODDS_REGIONS,
    ODDS_MARKETS,
    ODDS_SNAPSHOT_MAX_HOURS,
    CONSENSUS_OUTLIER_MAD_MULTIPLIER,
    CONSENSUS_MIN_OUTLIER_THRESHOLD,
)
from db import (
    check_api_budget,
    increment_api_budget,
    execute_query,
    fetch_one,
    fetch_all,
    generate_content_hash,
)

logger = logging.getLogger(__name__)


async def fetch_odds_from_api() -> Dict[str, Any]:
    """
    Fetch odds from The Odds API with budget checking
    
    Returns:
        Dict with status and data/error
    """
    # Check budget first
    can_call = await check_api_budget("the-odds-api", ODDS_MAX_CALLS_PER_DAY)
    if not can_call:
        logger.warning(f"API budget exhausted for the-odds-api (max {ODDS_MAX_CALLS_PER_DAY} calls/day)")
        return {
            "status": "budget_exceeded",
            "error": f"Daily API budget exceeded ({ODDS_MAX_CALLS_PER_DAY} calls)",
            "data": None
        }
    
    # Calculate date range: today + tomorrow only (in UTC)
    now_utc = datetime.now(timezone.utc)
    today_utc = now_utc.date()
    tomorrow_utc = today_utc + timedelta(days=1)
    commence_time_from = today_utc.isoformat() + "T00:00:00Z"
    commence_time_to = tomorrow_utc.isoformat() + "T23:59:59Z"
    
    # Build API request
    url = f"https://api.the-odds-api.com/v4/sports/{ODDS_SPORT_KEY}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": ODDS_REGIONS,
        "markets": ODDS_MARKETS,
        "bookmakers": ",".join(ODDS_BOOKMAKERS_ALLOWLIST[:3]),  # Max 3 bookmakers
        "oddsFormat": "decimal",
        "commenceTimeFrom": commence_time_from,
        "commenceTimeTo": commence_time_to,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Increment budget after successful call
            await increment_api_budget("the-odds-api")
            
            # Extract remaining calls from headers
            remaining_calls = response.headers.get("x-requests-remaining")
            used_calls = response.headers.get("x-requests-used")
            
            logger.info(
                f"Fetched odds from API: {len(data)} games, "
                f"remaining: {remaining_calls}, used: {used_calls}"
            )
            
            return {
                "status": "success",
                "data": data,
                "remaining_calls": remaining_calls,
                "used_calls": used_calls,
            }
            
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching odds: {e.response.status_code} - {e.response.text}")
        return {
            "status": "error",
            "error": f"HTTP {e.response.status_code}: {e.response.text}",
            "data": None
        }
    except Exception as e:
        logger.error(f"Error fetching odds from API: {e}")
        return {
            "status": "error",
            "error": str(e),
            "data": None
        }


async def store_odds_snapshot(
    game_id: str,
    bookmaker_key: str,
    market_type: str,
    outcome_name: Optional[str],
    team: Optional[str],
    point: Optional[float],
    price: float,
    ts: datetime,
) -> Dict[str, Any]:
    """
    Store odds snapshot with deduplication using content_hash
    
    Only stores if:
    - Content has changed (different content_hash), OR
    - More than ODDS_SNAPSHOT_MAX_HOURS have elapsed since last snapshot
    
    Args:
        game_id: Game identifier
        bookmaker_key: Bookmaker identifier (e.g., 'draftkings')
        market_type: Market type ('h2h', 'spread', 'totals')
        outcome_name: Outcome name for h2h market
        team: Team abbreviation for spread/totals
        point: Point value for spread/totals
        price: Decimal odds price
        ts: Timestamp of the odds
    
    Returns:
        Dict with status and action taken
    """
    # Generate content hash for deduplication
    content = {
        "game_id": game_id,
        "bookmaker_key": bookmaker_key,
        "market_type": market_type,
        "outcome_name": outcome_name,
        "team": team,
        "point": point,
        "price": price,
    }
    content_hash = generate_content_hash(content)
    
    # Check if we should store this snapshot
    check_query = """
        SELECT content_hash, ts
        FROM odds_snapshots
        WHERE game_id = $1 
          AND bookmaker_key = $2 
          AND market_type = $3
          AND COALESCE(outcome_name, '') = COALESCE($4, '')
          AND COALESCE(team, '') = COALESCE($5, '')
          AND COALESCE(point, 0) = COALESCE($6, 0)
        ORDER BY ts DESC
        LIMIT 1
    """
    
    last_snapshot = await fetch_one(
        check_query,
        game_id,
        bookmaker_key,
        market_type,
        outcome_name,
        team,
        point
    )
    
    # Determine if we should store
    should_store = False
    reason = None
    
    if last_snapshot is None:
        should_store = True
        reason = "first_snapshot"
    elif last_snapshot["content_hash"] != content_hash:
        should_store = True
        reason = "content_changed"
    else:
        # Check if max hours elapsed
        time_diff = ts - last_snapshot["ts"]
        hours_elapsed = time_diff.total_seconds() / 3600
        
        if hours_elapsed >= ODDS_SNAPSHOT_MAX_HOURS:
            should_store = True
            reason = f"time_elapsed_{hours_elapsed:.1f}h"
    
    if not should_store:
        return {
            "status": "skipped",
            "reason": "duplicate_within_threshold",
            "last_snapshot_ts": last_snapshot["ts"] if last_snapshot else None,
        }
    
    # Store the snapshot
    insert_query = """
        INSERT INTO odds_snapshots (
            game_id, bookmaker_key, market_type, outcome_name, 
            team, point, price, ts, content_hash
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (game_id, bookmaker_key, market_type, 
                     COALESCE(outcome_name, ''), COALESCE(team, ''), 
                     COALESCE(point, 0), price, ts)
        DO NOTHING
    """
    
    await execute_query(
        insert_query,
        game_id,
        bookmaker_key,
        market_type,
        outcome_name,
        team,
        point,
        price,
        ts,
        content_hash
    )
    
    logger.info(
        f"Stored odds snapshot for game={game_id}, bookmaker={bookmaker_key}, "
        f"market={market_type}, reason={reason}"
    )
    
    return {
        "status": "stored",
        "reason": reason,
        "content_hash": content_hash,
    }


async def get_consensus_line(
    game_id: str,
    market_type: str,
    team: Optional[str] = None,
    cutoff_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Build consensus line using median and MAD outlier removal
    
    Algorithm:
    1. Collect latest snapshot per bookmaker before cutoff
    2. Remove outliers using MAD: remove if |x - median| > max(0.5, 3*MAD)
    3. Return median point and corresponding price
    4. Track sample_count, used_bookmakers, outliers_removed
    
    Args:
        game_id: Game identifier
        market_type: Market type ('h2h', 'spread', 'totals')
        team: Team abbreviation (required for spread/h2h)
        cutoff_time: Time cutoff for snapshots (default: now)
    
    Returns:
        Dict with consensus line details or None if insufficient data
    """
    if cutoff_time is None:
        cutoff_time = datetime.now(timezone.utc)
    
    # Build query to get latest snapshot per bookmaker before cutoff
    query = """
        WITH latest_snapshots AS (
            SELECT DISTINCT ON (bookmaker_key)
                bookmaker_key,
                point,
                price,
                ts
            FROM odds_snapshots
            WHERE game_id = $1
              AND market_type = $2
              AND COALESCE(team, '') = COALESCE($3, '')
              AND ts <= $4
            ORDER BY bookmaker_key, ts DESC
        )
        SELECT * FROM latest_snapshots
        ORDER BY ts DESC
    """
    
    snapshots = await fetch_all(query, game_id, market_type, team, cutoff_time)
    
    if not snapshots:
        return {
            "status": "insufficient_data",
            "sample_count": 0,
            "consensus_point": None,
            "consensus_price": None,
        }
    
    # Extract points and prices
    points = [s["point"] for s in snapshots if s["point"] is not None]
    prices = [s["price"] for s in snapshots]
    bookmakers = [s["bookmaker_key"] for s in snapshots]
    
    if not points and market_type in ["spread", "totals"]:
        return {
            "status": "insufficient_data",
            "sample_count": len(snapshots),
            "consensus_point": None,
            "consensus_price": None,
        }
    
    # Calculate median
    # For spread/totals markets, we analyze points; for h2h, we analyze prices
    if points:
        median_point = statistics.median(points)
        metric_values = points  # Use points for spread/totals
        use_points_metric = True
    else:
        median_point = None
        metric_values = prices  # For h2h market, use prices as the metric
        use_points_metric = False
    
    median_price = statistics.median(prices)
    median_metric = median_point if use_points_metric else median_price
    
    # Remove outliers using MAD
    if len(metric_values) >= 3:
        # Calculate MAD (Median Absolute Deviation)
        deviations = [abs(val - median_metric) for val in metric_values]
        mad = statistics.median(deviations)
        
        # Threshold: max(0.5, 3*MAD)
        threshold = max(CONSENSUS_MIN_OUTLIER_THRESHOLD, CONSENSUS_OUTLIER_MAD_MULTIPLIER * mad)
        
        # Filter outliers
        filtered_data = []
        outliers_removed = []
        
        for i, snapshot in enumerate(snapshots):
            # Extract the same metric type we're analyzing (points or prices)
            metric_val = snapshot["point"] if use_points_metric else snapshot["price"]
            deviation = abs(metric_val - median_metric)
            
            if deviation <= threshold:
                filtered_data.append(snapshot)
            else:
                outliers_removed.append({
                    "bookmaker": snapshot["bookmaker_key"],
                    "point": snapshot["point"],
                    "price": snapshot["price"],
                    "deviation": deviation,
                })
        
        # Recalculate median after removing outliers
        if filtered_data:
            filtered_points = [s["point"] for s in filtered_data if s["point"] is not None]
            filtered_prices = [s["price"] for s in filtered_data]
            
            if filtered_points:
                median_point = statistics.median(filtered_points)
            median_price = statistics.median(filtered_prices)
            
            bookmakers = [s["bookmaker_key"] for s in filtered_data]
    else:
        outliers_removed = []
    
    return {
        "status": "success",
        "game_id": game_id,
        "market_type": market_type,
        "team": team,
        "consensus_point": median_point,
        "consensus_price": median_price,
        "sample_count": len(snapshots),
        "used_bookmakers": bookmakers,
        "outliers_removed": outliers_removed,
        "cutoff_time": cutoff_time,
    }


async def get_current_odds(
    game_id: str,
    market_type: Optional[str] = None,
    bookmaker_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get latest odds for a game
    
    Args:
        game_id: Game identifier
        market_type: Optional filter by market type
        bookmaker_key: Optional filter by bookmaker
    
    Returns:
        List of latest odds snapshots
    """
    query = """
        SELECT DISTINCT ON (bookmaker_key, market_type, COALESCE(team, ''), COALESCE(outcome_name, ''))
            id, game_id, bookmaker_key, market_type, outcome_name,
            team, point, price, ts, created_at
        FROM odds_snapshots
        WHERE game_id = $1
    """
    
    params = [game_id]
    param_idx = 2
    
    if market_type:
        query += f" AND market_type = ${param_idx}"
        params.append(market_type)
        param_idx += 1
    
    if bookmaker_key:
        query += f" AND bookmaker_key = ${param_idx}"
        params.append(bookmaker_key)
        param_idx += 1
    
    query += """
        ORDER BY bookmaker_key, market_type, COALESCE(team, ''), 
                 COALESCE(outcome_name, ''), ts DESC
    """
    
    odds = await fetch_all(query, *params)
    
    return odds


async def get_odds_movement(
    game_id: str,
    market_type: str,
    team: Optional[str] = None,
    bookmaker_key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get historical odds movement for a game
    
    Args:
        game_id: Game identifier
        market_type: Market type ('h2h', 'spread', 'totals')
        team: Optional team filter
        bookmaker_key: Optional bookmaker filter
    
    Returns:
        List of odds snapshots ordered by timestamp
    """
    query = """
        SELECT 
            id, game_id, bookmaker_key, market_type, outcome_name,
            team, point, price, ts, created_at
        FROM odds_snapshots
        WHERE game_id = $1
          AND market_type = $2
    """
    
    params = [game_id, market_type]
    param_idx = 3
    
    if team:
        query += f" AND COALESCE(team, '') = ${param_idx}"
        params.append(team)
        param_idx += 1
    
    if bookmaker_key:
        query += f" AND bookmaker_key = ${param_idx}"
        params.append(bookmaker_key)
        param_idx += 1
    
    query += " ORDER BY ts ASC"
    
    movement = await fetch_all(query, *params)
    
    return movement
