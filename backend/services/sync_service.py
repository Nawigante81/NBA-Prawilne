"""
NBA Betting Analytics Backend - Sync Service
Orchestrates all synchronization jobs using APScheduler
"""
import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

# Import settings
import settings as config

# Import service modules
from services import stats_service
from services import odds_service
from services import betting_stats_service
from services import clv_service
from db import clear_expired_cache

# Configure logging
logger = logging.getLogger(__name__)


def setup_scheduler() -> AsyncIOScheduler:
    """
    Initialize and configure APScheduler with all sync jobs.
    
    Returns:
        AsyncIOScheduler: Configured and started scheduler instance
    """
    logger.info("Setting up APScheduler...")
    
    # Create scheduler with timezone from settings
    timezone = pytz.timezone(config.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=timezone)
    
    # Add job: sync_nba_stats every SYNC_NBA_STATS_INTERVAL_HOURS hours
    scheduler.add_job(
        sync_nba_stats,
        trigger=IntervalTrigger(hours=config.SYNC_NBA_STATS_INTERVAL_HOURS),
        id='sync_nba_stats',
        name='Sync NBA Stats',
        replace_existing=True,
        max_instances=1
    )
    logger.info(f"Added job: sync_nba_stats (every {config.SYNC_NBA_STATS_INTERVAL_HOURS} hours)")
    
    # Add job: sync_odds every SYNC_ODDS_INTERVAL_MINUTES minutes
    scheduler.add_job(
        sync_odds,
        trigger=IntervalTrigger(minutes=config.SYNC_ODDS_INTERVAL_MINUTES),
        id='sync_odds',
        name='Sync Odds',
        replace_existing=True,
        max_instances=1
    )
    logger.info(f"Added job: sync_odds (every {config.SYNC_ODDS_INTERVAL_MINUTES} minutes)")
    
    # Add job: compute_results every COMPUTE_RESULTS_INTERVAL_HOURS hours
    scheduler.add_job(
        compute_results,
        trigger=IntervalTrigger(hours=config.COMPUTE_RESULTS_INTERVAL_HOURS),
        id='compute_results',
        name='Compute Results',
        replace_existing=True,
        max_instances=1
    )
    logger.info(f"Added job: compute_results (every {config.COMPUTE_RESULTS_INTERVAL_HOURS} hours)")
    
    # Add job: compute_closing_lines_job every 1 hour
    scheduler.add_job(
        compute_closing_lines_job,
        trigger=IntervalTrigger(hours=1),
        id='compute_closing_lines',
        name='Compute Closing Lines',
        replace_existing=True,
        max_instances=1
    )
    logger.info("Added job: compute_closing_lines (every 1 hour)")
    
    # Add job: clear_expired_cache every 6 hours
    scheduler.add_job(
        clear_expired_cache,
        trigger=IntervalTrigger(hours=6),
        id='clear_expired_cache',
        name='Clear Expired Cache',
        replace_existing=True,
        max_instances=1
    )
    logger.info("Added job: clear_expired_cache (every 6 hours)")
    
    # Start the scheduler
    scheduler.start()
    logger.info("APScheduler started successfully")
    
    return scheduler


async def sync_nba_stats() -> None:
    """
    Main NBA stats sync job.
    Orchestrates syncing teams, games, results, and stats.
    """
    logger.info("=== Starting NBA Stats Sync ===")
    
    try:
        # Sync NBA teams
        logger.info("Step 1/5: Syncing NBA teams...")
        teams_result = await stats_service.sync_nba_teams()
        logger.info(f"✓ Teams synced: {teams_result.get('teams_updated', 0)} updated")
    except Exception as e:
        logger.error(f"✗ Failed to sync NBA teams: {e}", exc_info=True)
    
    try:
        # Sync NBA games
        logger.info("Step 2/5: Syncing NBA games...")
        games_result = await stats_service.sync_nba_games()
        logger.info(f"✓ Games synced: {games_result.get('games_created', 0)} created, "
                   f"{games_result.get('games_updated', 0)} updated")
    except Exception as e:
        logger.error(f"✗ Failed to sync NBA games: {e}", exc_info=True)
    
    try:
        # Sync game results
        logger.info("Step 3/5: Syncing game results...")
        results_result = await stats_service.sync_game_results()
        logger.info(f"✓ Game results synced: {results_result.get('games_updated', 0)} updated")
    except Exception as e:
        logger.error(f"✗ Failed to sync game results: {e}", exc_info=True)
    
    try:
        # Sync team stats
        logger.info("Step 4/5: Syncing team stats...")
        team_stats_result = await stats_service.sync_team_stats()
        logger.info(f"✓ Team stats synced: {team_stats_result.get('stats_updated', 0)} updated")
    except Exception as e:
        logger.error(f"✗ Failed to sync team stats: {e}", exc_info=True)
    
    try:
        # Sync player stats
        logger.info("Step 5/5: Syncing player stats...")
        player_stats_result = await stats_service.sync_player_stats()
        logger.info(f"✓ Player stats synced: {player_stats_result.get('stats_updated', 0)} updated")
    except Exception as e:
        logger.error(f"✗ Failed to sync player stats: {e}", exc_info=True)
    
    logger.info("=== NBA Stats Sync Complete ===")


async def sync_odds() -> None:
    """
    Main odds sync job.
    Fetches odds from API and stores snapshots if within budget.
    """
    logger.info("=== Starting Odds Sync ===")
    
    try:
        # Fetch odds from API
        logger.info("Fetching odds from API...")
        odds_result = await odds_service.fetch_odds_from_api()
        
        if not odds_result.get('success'):
            logger.error(f"✗ Failed to fetch odds: {odds_result.get('error')}")
            return
        
        games_data = odds_result.get('games', [])
        logger.info(f"✓ Fetched odds for {len(games_data)} games")
        
        # Log budget status
        api_calls_used = odds_result.get('api_calls_used', 0)
        api_calls_remaining = odds_result.get('api_calls_remaining', 0)
        logger.info(f"API Budget: {api_calls_used} used, {api_calls_remaining} remaining")
        
        # Store snapshots if within budget and data available
        if api_calls_remaining > 0 and games_data:
            logger.info("Storing odds snapshots...")
            snapshot_count = 0
            
            for game in games_data:
                try:
                    game_id = game.get('id')
                    if game_id:
                        await odds_service.store_odds_snapshot(game_id, game)
                        snapshot_count += 1
                except Exception as e:
                    logger.error(f"Failed to store snapshot for game {game.get('id')}: {e}")
            
            logger.info(f"✓ Stored {snapshot_count} odds snapshots")
        else:
            logger.warning("Skipping snapshot storage (out of budget or no data)")
        
    except Exception as e:
        logger.error(f"✗ Odds sync failed: {e}", exc_info=True)
    
    logger.info("=== Odds Sync Complete ===")


async def compute_results() -> None:
    """
    Compute ATS/O-U results for all games.
    """
    logger.info("=== Starting Results Computation ===")
    
    try:
        logger.info("Computing ATS/O-U results for all games...")
        results = await betting_stats_service.compute_all_game_results()
        
        games_processed = results.get('games_processed', 0)
        games_updated = results.get('games_updated', 0)
        
        logger.info(f"✓ Results computed: {games_processed} games processed, "
                   f"{games_updated} updated")
        
    except Exception as e:
        logger.error(f"✗ Failed to compute results: {e}", exc_info=True)
    
    logger.info("=== Results Computation Complete ===")


async def compute_closing_lines_job() -> None:
    """
    Compute closing lines for finished games.
    """
    logger.info("=== Starting Closing Lines Computation ===")
    
    try:
        logger.info("Computing closing lines for finished games...")
        lines_computed = await clv_service.compute_all_closing_lines()
        
        logger.info(f"✓ Closing lines computed: {lines_computed} games processed")
        
    except Exception as e:
        logger.error(f"✗ Failed to compute closing lines: {e}", exc_info=True)
    
    logger.info("=== Closing Lines Computation Complete ===")


async def clear_expired_cache() -> None:
    """
    Clear expired cache entries.
    This is a placeholder for future cache management.
    """
    logger.info("=== Starting Cache Cleanup ===")
    
    try:
        # TODO: Implement cache cleanup logic when caching is added
        logger.info("Cache cleanup not yet implemented")
        
    except Exception as e:
        logger.error(f"✗ Failed to clear cache: {e}", exc_info=True)
    
    logger.info("=== Cache Cleanup Complete ===")


def shutdown_scheduler(scheduler: AsyncIOScheduler) -> None:
    """
    Gracefully shutdown the scheduler.
    Waits for running jobs to complete.
    
    Args:
        scheduler: The scheduler instance to shutdown
    """
    logger.info("Shutting down scheduler...")
    
    try:
        # Wait for running jobs to complete
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}", exc_info=True)
