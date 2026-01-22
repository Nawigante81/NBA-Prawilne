"""
NBA Stats provider using nba_api library.
Implements caching and rate limiting for NBA Stats endpoints.
"""
import asyncio
import hashlib
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.static import players as nba_players
from nba_api.stats.endpoints import scoreboardv2, playergamelog, teamgamelog, leaguegamefinder
from providers.base import BaseProvider
from models import Team, Player, Game, PlayerGameStat, TeamGameStat
from services.budget_service import get_budget_service
from settings import settings
import logging

logger = logging.getLogger(__name__)


class NBAStatsProvider(BaseProvider):
    """Provider for NBA Stats using nba_api library."""
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.budget_service = get_budget_service()
        self._semaphore = asyncio.Semaphore(settings.nba_api_max_concurrent)
    
    async def _check_cache(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Check if cached response exists and is valid."""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        result = self.db.table("api_cache").select("*").eq("provider", "nba_api").eq("endpoint", endpoint).eq("params_hash", params_hash).execute()
        
        if result.data and len(result.data) > 0:
            entry = result.data[0]
            expires_at = datetime.fromisoformat(entry["expires_at"].replace("Z", "+00:00"))
            
            if datetime.utcnow() < expires_at.replace(tzinfo=None):
                logger.info(f"Cache hit for {endpoint}")
                return entry["response_data"]
        
        return None
    
    async def _store_cache(self, endpoint: str, params: Dict, response_data: Dict, ttl_seconds: int):
        """Store response in cache."""
        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        # Upsert cache entry
        self.db.table("api_cache").upsert({
            "provider": "nba_api",
            "endpoint": endpoint,
            "params_hash": params_hash,
            "response_data": response_data,
            "ttl_seconds": ttl_seconds,
            "cached_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }, on_conflict="provider,endpoint,params_hash").execute()
    
    async def _rate_limited_fetch(self, fetch_func, *args, **kwargs):
        """Execute fetch with rate limiting."""
        async with self._semaphore:
            # Check budget
            budget_check = await self.budget_service.check_budget("nba_api")
            if not budget_check["allowed"]:
                raise Exception("NBA API daily budget exceeded")
            
            # Execute in thread pool (nba_api is synchronous)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: fetch_func(*args, **kwargs))
            
            # Increment budget
            await self.budget_service.increment_calls("nba_api", 1)
            
            # Small delay to be polite
            await asyncio.sleep(0.5)
            
            return result
    
    async def fetch_teams(self) -> List[Dict]:
        """Fetch all NBA teams."""
        endpoint = "teams"
        params = {}
        
        # Check cache (7 day TTL)
        cached = await self._check_cache(endpoint, params)
        if cached:
            return cached["teams"]
        
        # Fetch from API
        teams_data = await self._rate_limited_fetch(nba_teams.get_teams)
        
        # Store in cache
        await self._store_cache(endpoint, params, {"teams": teams_data}, ttl_seconds=settings.nba_api_players_ttl_days * 24 * 3600)
        
        return teams_data
    
    async def fetch_players(self) -> List[Dict]:
        """Fetch all NBA players."""
        endpoint = "players"
        params = {}
        
        # Check cache (7 day TTL)
        cached = await self._check_cache(endpoint, params)
        if cached:
            return cached["players"]
        
        # Fetch from API
        players_data = await self._rate_limited_fetch(nba_players.get_players)
        
        # Store in cache
        await self._store_cache(endpoint, params, {"players": players_data}, ttl_seconds=settings.nba_api_players_ttl_days * 24 * 3600)
        
        return players_data
    
    async def fetch_scoreboard(self, game_date: Optional[date] = None) -> Dict:
        """Fetch scoreboard for a specific date."""
        if game_date is None:
            game_date = date.today()
        
        endpoint = "scoreboard"
        params = {"game_date": game_date.strftime("%Y-%m-%d")}
        
        # Check cache (1 hour TTL)
        cached = await self._check_cache(endpoint, params)
        if cached:
            return cached
        
        # Fetch from API
        scoreboard = await self._rate_limited_fetch(
            scoreboardv2.ScoreboardV2,
            game_date=game_date.strftime("%m/%d/%Y")
        )
        
        data = scoreboard.get_dict()
        
        # Store in cache
        await self._store_cache(endpoint, params, data, ttl_seconds=settings.nba_api_scoreboard_ttl_hours * 3600)
        
        return data
    
    async def fetch_player_game_log(self, player_id: int, season: str = "2024-25") -> List[Dict]:
        """Fetch game log for a player."""
        endpoint = "player_game_log"
        params = {"player_id": player_id, "season": season}
        
        # Check cache (6 hour TTL)
        cached = await self._check_cache(endpoint, params)
        if cached:
            return cached["games"]
        
        # Fetch from API
        gamelog = await self._rate_limited_fetch(
            playergamelog.PlayerGameLog,
            player_id=player_id,
            season=season
        )
        
        games = gamelog.get_dict()["resultSets"][0]["rowSet"]
        
        # Store in cache
        await self._store_cache(endpoint, params, {"games": games}, ttl_seconds=settings.nba_api_gamelogs_ttl_hours * 3600)
        
        return games
    
    async def fetch(self, resource: str = "teams", **kwargs) -> Any:
        """
        Fetch data from NBA Stats API.
        
        Args:
            resource: "teams", "players", "scoreboard", "player_game_log"
            **kwargs: Additional parameters
        """
        if resource == "teams":
            return await self.fetch_teams()
        elif resource == "players":
            return await self.fetch_players()
        elif resource == "scoreboard":
            game_date = kwargs.get("game_date")
            return await self.fetch_scoreboard(game_date)
        elif resource == "player_game_log":
            player_id = kwargs.get("player_id")
            season = kwargs.get("season", "2024-25")
            return await self.fetch_player_game_log(player_id, season)
        else:
            raise ValueError(f"Unknown resource: {resource}")
    
    def normalize(self, raw_data: Any) -> List[Any]:
        """Normalize NBA Stats data to Pydantic models."""
        # This method is resource-dependent
        # Actual normalization happens in resource-specific methods
        return []
    
    def normalize_teams(self, teams_data: List[Dict]) -> List[Team]:
        """Normalize teams data."""
        teams = []
        for team_dict in teams_data:
            team = Team(
                abbreviation=team_dict["abbreviation"],
                full_name=team_dict["full_name"],
                name=team_dict["nickname"],
                city=team_dict["city"]
            )
            teams.append(team)
        return teams
    
    def normalize_players(self, players_data: List[Dict], team_map: Dict[int, str]) -> List[Player]:
        """Normalize players data."""
        players = []
        for player_dict in players_data:
            if not player_dict.get("is_active", True):
                continue
            
            team_id = player_dict.get("team_id")
            team_abbr = team_map.get(team_id, "UNK")
            
            player = Player(
                name=player_dict["full_name"],
                player_id=player_dict["id"],
                team_abbreviation=team_abbr,
                is_active=player_dict.get("is_active", True)
            )
            players.append(player)
        return players
    
    async def upsert(self, normalized_data: List[Any]) -> Dict[str, int]:
        """Upsert normalized data to database."""
        if not normalized_data:
            return {"inserted": 0, "updated": 0, "errors": 0}
        
        # Determine table based on model type
        first_item = normalized_data[0]
        
        if isinstance(first_item, Team):
            table = "teams"
            conflict_column = "abbreviation"
        elif isinstance(first_item, Player):
            table = "players"
            conflict_column = "name,team_abbreviation,season_year"
        else:
            return {"inserted": 0, "updated": 0, "errors": 0}
        
        # Convert to dicts
        data_dicts = [item.model_dump(exclude_none=True) for item in normalized_data]
        
        # Upsert
        try:
            result = self.db.table(table).upsert(data_dicts, on_conflict=conflict_column).execute()
            return {"inserted": len(result.data), "updated": 0, "errors": 0}
        except Exception as e:
            self.logger.error(f"Upsert failed: {str(e)}")
            return {"inserted": 0, "updated": 0, "errors": len(data_dicts)}
    
    async def healthcheck(self) -> Dict[str, Any]:
        """Check NBA Stats API health."""
        try:
            # Try to fetch teams (uses cache if available)
            teams = await self.fetch_teams()
            return {
                "healthy": True,
                "message": "NBA Stats API accessible",
                "details": {"teams_count": len(teams)}
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"NBA Stats API error: {str(e)}",
                "details": {}
            }
