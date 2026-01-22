"""
Synchronization service for orchestrating all data providers.
Handles startup sync, scheduled syncs, and Bulls-specific roster updates.
"""
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from db import get_db
from settings import settings
from providers.nba_stats import NBAStatsProvider
from providers.odds_api import OddsAPIProvider
from providers.basketball_reference import BasketballReferenceProvider
from services.budget_service import get_budget_service
from services.clv_service import get_clv_service
import logging

logger = logging.getLogger(__name__)


class SyncService:
    """Service for orchestrating data synchronization across all providers."""
    
    def __init__(self):
        self.db = get_db()
        self.budget_service = get_budget_service()
        self.clv_service = get_clv_service()
        
        # Initialize providers
        self.nba_stats = NBAStatsProvider(self.db)
        self.odds_api = OddsAPIProvider(self.db)
        self.basketball_ref = BasketballReferenceProvider(self.db)
    
    async def startup_sync(self) -> Dict[str, Any]:
        """
        Run comprehensive sync on application startup.
        Syncs teams, players, games for today/tomorrow, and odds if within budget.
        
        Returns:
            Dictionary with sync results for each provider
        """
        logger.info("=== Starting startup sync ===")
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "teams": None,
            "players": None,
            "games": None,
            "odds": None,
            "bulls_roster": None
        }
        
        try:
            # 1. Sync teams (rarely changes, but foundation for other data)
            logger.info("Syncing teams...")
            try:
                teams_result = await self.nba_stats.sync(resource="teams")
                results["teams"] = teams_result
                logger.info(f"Teams sync: {teams_result.get('items_processed', 0)} processed")
            except Exception as e:
                logger.error(f"Teams sync failed: {str(e)}", exc_info=True)
                results["teams"] = {"success": False, "error": str(e)}
            
            # 2. Sync players (all active players)
            logger.info("Syncing players...")
            try:
                players_result = await self.nba_stats.sync(resource="players")
                results["players"] = players_result
                logger.info(f"Players sync: {players_result.get('items_processed', 0)} processed")
            except Exception as e:
                logger.error(f"Players sync failed: {str(e)}", exc_info=True)
                results["players"] = {"success": False, "error": str(e)}
            
            # 3. Sync games for today and tomorrow
            logger.info("Syncing games (today and tomorrow)...")
            try:
                today = date.today()
                tomorrow = today + timedelta(days=1)
                
                games_today = await self.nba_stats.sync(resource="scoreboard", game_date=today)
                games_tomorrow = await self.nba_stats.sync(resource="scoreboard", game_date=tomorrow)
                
                results["games"] = {
                    "success": True,
                    "today": games_today,
                    "tomorrow": games_tomorrow
                }
                logger.info(
                    f"Games sync: {games_today.get('items_processed', 0)} today, "
                    f"{games_tomorrow.get('items_processed', 0)} tomorrow"
                )
            except Exception as e:
                logger.error(f"Games sync failed: {str(e)}", exc_info=True)
                results["games"] = {"success": False, "error": str(e)}
            
            # 4. Sync odds (if budget allows)
            logger.info("Checking odds budget...")
            try:
                should_fetch = await self.odds_api.should_fetch_odds()
                
                if should_fetch:
                    logger.info("Syncing odds...")
                    odds_result = await self.odds_api.sync(
                        window_days=settings.odds_game_window_days
                    )
                    results["odds"] = odds_result
                    logger.info(f"Odds sync: {odds_result.get('items_processed', 0)} processed")
                else:
                    budget_check = await self.budget_service.check_budget("odds_api")
                    results["odds"] = {
                        "success": True,
                        "skipped": True,
                        "reason": f"Budget limit reached: {budget_check['calls_made']}/{budget_check['calls_limit']}"
                    }
                    logger.info("Odds sync skipped: budget limit reached")
            except Exception as e:
                logger.error(f"Odds sync failed: {str(e)}", exc_info=True)
                results["odds"] = {"success": False, "error": str(e)}
            
            # 5. Special sync for Bulls roster (Basketball-Reference data)
            logger.info("Syncing Bulls roster...")
            try:
                bulls_result = await self.sync_bulls_roster()
                results["bulls_roster"] = bulls_result
                logger.info(f"Bulls roster sync: {bulls_result.get('players_synced', 0)} players")
            except Exception as e:
                logger.error(f"Bulls roster sync failed: {str(e)}", exc_info=True)
                results["bulls_roster"] = {"success": False, "error": str(e)}
            
            logger.info("=== Startup sync completed ===")
            return results
        
        except Exception as e:
            logger.error(f"Startup sync failed: {str(e)}", exc_info=True)
            results["error"] = str(e)
            return results
    
    async def scheduled_sync(self) -> Dict[str, Any]:
        """
        Run scheduled sync (every 12 hours).
        Refreshes games, stats, and odds (if budget allows).
        
        Returns:
            Dictionary with sync results
        """
        logger.info("=== Starting scheduled sync ===")
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "games": None,
            "player_stats": None,
            "team_stats": None,
            "odds": None
        }
        
        try:
            # 1. Refresh games for upcoming window
            logger.info("Refreshing games...")
            try:
                today = date.today()
                game_dates = [today + timedelta(days=i) for i in range(settings.odds_game_window_days)]
                
                games_results = []
                for game_date in game_dates:
                    result = await self.nba_stats.sync(resource="scoreboard", game_date=game_date)
                    games_results.append(result)
                
                results["games"] = {
                    "success": True,
                    "dates_synced": [str(d) for d in game_dates],
                    "results": games_results
                }
                logger.info(f"Games refreshed for {len(game_dates)} dates")
            except Exception as e:
                logger.error(f"Games refresh failed: {str(e)}", exc_info=True)
                results["games"] = {"success": False, "error": str(e)}
            
            # 2. Sync recent player game logs for active players
            logger.info("Syncing player game logs...")
            try:
                player_stats_result = await self._sync_recent_player_stats()
                results["player_stats"] = player_stats_result
                logger.info(f"Player stats: {player_stats_result.get('players_synced', 0)} players")
            except Exception as e:
                logger.error(f"Player stats sync failed: {str(e)}", exc_info=True)
                results["player_stats"] = {"success": False, "error": str(e)}
            
            # 3. Sync recent team game logs
            logger.info("Syncing team game logs...")
            try:
                team_stats_result = await self._sync_recent_team_stats()
                results["team_stats"] = team_stats_result
                logger.info(f"Team stats: {team_stats_result.get('teams_synced', 0)} teams")
            except Exception as e:
                logger.error(f"Team stats sync failed: {str(e)}", exc_info=True)
                results["team_stats"] = {"success": False, "error": str(e)}
            
            # 4. Refresh odds if budget allows
            logger.info("Checking odds budget...")
            try:
                budget_check = await self.budget_service.check_budget("odds_api")
                
                if budget_check["allowed"]:
                    logger.info("Refreshing odds...")
                    odds_result = await self.odds_api.sync(
                        window_days=settings.odds_game_window_days
                    )
                    results["odds"] = odds_result
                    logger.info(f"Odds refreshed: {odds_result.get('items_processed', 0)} processed")
                else:
                    results["odds"] = {
                        "success": True,
                        "skipped": True,
                        "reason": f"Budget exhausted: {budget_check['calls_made']}/{budget_check['calls_limit']}"
                    }
                    logger.info("Odds refresh skipped: budget exhausted")
            except Exception as e:
                logger.error(f"Odds refresh failed: {str(e)}", exc_info=True)
                results["odds"] = {"success": False, "error": str(e)}
            
            logger.info("=== Scheduled sync completed ===")
            return results
        
        except Exception as e:
            logger.error(f"Scheduled sync failed: {str(e)}", exc_info=True)
            results["error"] = str(e)
            return results
    
    async def sync_bulls_roster(self) -> Dict[str, Any]:
        """
        Special sync for Bulls players using Basketball-Reference.
        Enriches player data with detailed info from BR.
        
        Returns:
            Dictionary with sync results
        """
        logger.info("Starting Bulls roster sync...")
        
        try:
            # Sync Bulls roster from Basketball-Reference
            result = await self.basketball_ref.sync(resource="roster", team_abbr="CHI")
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "players_synced": 0
                }
            
            # Also sync Bulls players from NBA Stats for cross-reference
            try:
                # Get all players, then filter Bulls in post-processing
                all_players = await self.nba_stats.fetch(resource="players")
                bulls_players = [p for p in all_players if p.get("team_abbreviation") == "CHI"]
                
                if bulls_players:
                    normalized = self.nba_stats.normalize(bulls_players)
                    await self.nba_stats.upsert(normalized)
                    logger.info(f"Cross-referenced {len(normalized)} Bulls players from NBA Stats")
            except Exception as e:
                logger.warning(f"Bulls NBA Stats cross-reference failed: {str(e)}")
            
            return {
                "success": True,
                "players_synced": result.get("items_processed", 0),
                "provider": "Basketball-Reference",
                "team": "CHI"
            }
        
        except Exception as e:
            logger.error(f"Bulls roster sync failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "players_synced": 0
            }
    
    async def _sync_recent_player_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Sync recent player game logs.
        
        Args:
            days: Number of days of history to sync
        
        Returns:
            Dictionary with sync results
        """
        try:
            # Get active players (limit to reduce API calls)
            players_result = self.db.table("players").select("id,player_id,name,team_abbreviation").eq(
                "is_active", True
            ).limit(100).execute()  # Limit to avoid excessive API calls
            
            if not players_result.data:
                return {
                    "success": True,
                    "players_synced": 0,
                    "message": "No active players found"
                }
            
            synced_count = 0
            errors = []
            
            for player in players_result.data:
                player_id = player.get("player_id")
                
                if not player_id:
                    continue
                
                try:
                    # Fetch and sync player game log
                    result = await self.nba_stats.sync(
                        resource="player_gamelog",
                        player_id=player_id
                    )
                    
                    if result.get("success"):
                        synced_count += 1
                except Exception as e:
                    errors.append({
                        "player": player.get("name"),
                        "error": str(e)
                    })
                    logger.warning(f"Failed to sync stats for {player.get('name')}: {str(e)}")
            
            return {
                "success": True,
                "players_synced": synced_count,
                "total_players": len(players_result.data),
                "errors": errors[:10]  # Limit error list
            }
        
        except Exception as e:
            logger.error(f"Error syncing player stats: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "players_synced": 0
            }
    
    async def _sync_recent_team_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Sync recent team game logs.
        
        Args:
            days: Number of days of history to sync
        
        Returns:
            Dictionary with sync results
        """
        try:
            # Get all teams
            teams_result = self.db.table("teams").select("id,abbreviation,full_name").execute()
            
            if not teams_result.data:
                return {
                    "success": True,
                    "teams_synced": 0,
                    "message": "No teams found"
                }
            
            synced_count = 0
            errors = []
            
            for team in teams_result.data:
                team_abbr = team.get("abbreviation")
                
                try:
                    # Fetch and sync team game log
                    result = await self.nba_stats.sync(
                        resource="team_gamelog",
                        team_abbreviation=team_abbr
                    )
                    
                    if result.get("success"):
                        synced_count += 1
                except Exception as e:
                    errors.append({
                        "team": team_abbr,
                        "error": str(e)
                    })
                    logger.warning(f"Failed to sync stats for {team_abbr}: {str(e)}")
            
            return {
                "success": True,
                "teams_synced": synced_count,
                "total_teams": len(teams_result.data),
                "errors": errors[:10]
            }
        
        except Exception as e:
            logger.error(f"Error syncing team stats: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "teams_synced": 0
            }
    
    async def healthcheck_all_providers(self) -> Dict[str, Any]:
        """
        Check health of all providers.
        
        Returns:
            Dictionary with health status for each provider
        """
        logger.info("Running provider health checks...")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "nba_stats": None,
            "odds_api": None,
            "basketball_reference": None
        }
        
        try:
            # Check NBA Stats
            try:
                nba_health = await self.nba_stats.healthcheck()
                results["nba_stats"] = nba_health
            except Exception as e:
                results["nba_stats"] = {
                    "healthy": False,
                    "message": str(e)
                }
            
            # Check Odds API
            try:
                odds_health = await self.odds_api.healthcheck()
                results["odds_api"] = odds_health
            except Exception as e:
                results["odds_api"] = {
                    "healthy": False,
                    "message": str(e)
                }
            
            # Check Basketball-Reference
            try:
                br_health = await self.basketball_ref.healthcheck()
                results["basketball_reference"] = br_health
            except Exception as e:
                results["basketball_reference"] = {
                    "healthy": False,
                    "message": str(e)
                }
            
            # Overall health
            all_healthy = all(
                r and r.get("healthy") 
                for r in [results["nba_stats"], results["odds_api"], results["basketball_reference"]]
            )
            
            results["overall_healthy"] = all_healthy
            
            logger.info(f"Health check complete: {'All systems operational' if all_healthy else 'Some systems down'}")
            
            return results
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "overall_healthy": False,
                "error": str(e)
            }


# Global instance
_sync_service: Optional[SyncService] = None


def get_sync_service() -> SyncService:
    """Get or create sync service singleton."""
    global _sync_service
    if _sync_service is None:
        _sync_service = SyncService()
    return _sync_service
