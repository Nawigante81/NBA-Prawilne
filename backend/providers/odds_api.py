"""
The Odds API provider with strict budget enforcement.
"""
import asyncio
import hashlib
import json
import httpx
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from models import Game, OddsSnapshot
from services.budget_service import get_budget_service
from services.clv_service import get_clv_service
from services.odds_service import normalize_market_type
from settings import settings
import logging

logger = logging.getLogger(__name__)


class OddsAPIProvider(BaseProvider):
    """Provider for The Odds API with budget enforcement."""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self.budget_service = get_budget_service()
        self.clv_service = get_clv_service()
        self.api_key = settings.odds_api_key
        
        if not self.api_key:
            logger.warning("Odds API key not configured")
    
    async def _can_fetch_odds(self) -> bool:
        """Check if we can fetch odds within budget."""
        budget_check = await self.budget_service.check_budget("odds_api")
        
        if not budget_check["allowed"]:
            logger.warning(f"Odds API budget exceeded: {budget_check['calls_made']}/{budget_check['calls_limit']}")
            return False
        
        return True
    
    async def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make HTTP request to Odds API with retry logic."""
        url = f"{self.BASE_URL}/{endpoint}"
        params["apiKey"] = self.api_key

        # Cache lookup
        params_hash = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()
        cache = self.db.table("api_cache").select("response_data,expires_at").eq(
            "provider", "odds_api"
        ).eq("endpoint", endpoint).eq("params_hash", params_hash).execute()
        if cache.data:
            cached = cache.data[0]
            expires_at = cached.get("expires_at")
            if expires_at:
                expires_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expires_dt > datetime.utcnow():
                    return cached.get("response_data") or {}
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 200:
                        # Increment budget
                        await self.budget_service.increment_calls("odds_api", 1)
                        payload = response.json()
                        # Save cache (6h)
                        ttl_seconds = 6 * 3600
                        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
                        self.db.table("api_cache").upsert({
                            "provider": "odds_api",
                            "endpoint": endpoint,
                            "params_hash": params_hash,
                            "response_data": payload,
                            "ttl_seconds": ttl_seconds,
                            "cached_at": datetime.utcnow().isoformat(),
                            "expires_at": expires_at.isoformat(),
                        }, on_conflict="provider,endpoint,params_hash").execute()
                        return payload
                    
                    elif response.status_code == 429:
                        # Rate limit hit
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limit hit, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    
                    else:
                        logger.error(f"Odds API error: {response.status_code} {response.text}")
                        raise Exception(f"Odds API returned {response.status_code}")
                
            except httpx.TimeoutException:
                wait_time = 2 ** attempt
                logger.warning(f"Timeout, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Error: {str(e)}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
        
        raise Exception("Max retries exceeded")
    
    async def fetch_upcoming_games(self, window_days: Optional[int] = None) -> List[Dict]:
        """
        Fetch upcoming NBA games within the window.
        
        Args:
            window_days: How many days ahead to fetch (default: from settings)
        """
        if window_days is None:
            window_days = settings.odds_game_window_days
        
        # Check budget first
        if not await self._can_fetch_odds():
            logger.warning("Skipping odds fetch - budget exceeded")
            return []
        
        endpoint = "sports/basketball_nba/odds"
        
        # Calculate date range
        commence_time_from = datetime.utcnow().isoformat()
        commence_time_to = (datetime.utcnow() + timedelta(days=window_days)).isoformat()
        
        allowlist = settings.odds_bookmakers_allowlist[:3]
        params = {
            "regions": "us",
            "markets": ",".join(["h2h", "spreads", "totals"]),
            "bookmakers": ",".join(allowlist),
            "commenceTimeFrom": commence_time_from,
            "commenceTimeTo": commence_time_to,
            "oddsFormat": "american"
        }
        
        logger.info(f"Fetching odds for games from {commence_time_from} to {commence_time_to}")
        
        data = await self._make_request(endpoint, params)
        return data
    
    async def fetch(self, **kwargs) -> Any:
        """Fetch odds data."""
        window_days = kwargs.get("window_days")
        return await self.fetch_upcoming_games(window_days)
    
    def normalize(self, raw_data: Any) -> List[Any]:
        """
        Normalize Odds API response to Games and OddsSnapshots.
        
        Returns:
            List of (Game, List[OddsSnapshot]) tuples
        """
        if not raw_data:
            return []
        
        results = []
        snapshot_time = datetime.utcnow()
        
        for game_data in raw_data:
            # Create Game object
            game = Game(
                id=game_data["id"],
                sport_key=game_data["sport_key"],
                sport_title=game_data["sport_title"],
                commence_time=datetime.fromisoformat(game_data["commence_time"].replace("Z", "+00:00")),
                home_team=game_data["home_team"],
                away_team=game_data["away_team"]
            )
            
            # Create OddsSnapshots
            snapshots = []
            
            for bookmaker in game_data.get("bookmakers", []):
                bookmaker_key = bookmaker["key"]
                bookmaker_title = bookmaker["title"]
                
                for market in bookmaker.get("markets", []):
                    market_type = normalize_market_type(market.get("key"))
                    
                    for outcome in market.get("outcomes", []):
                        team_name = outcome.get("name") if market_type in ["h2h", "spreads"] else None
                        snapshot = OddsSnapshot(
                            game_id=game.id,
                            bookmaker_key=bookmaker_key,
                            bookmaker_title=bookmaker_title,
                            market_type=market_type,
                            outcome_name=outcome.get("name"),
                            team=team_name,
                            point=outcome.get("point"),
                            price=outcome.get("price"),
                            ts=snapshot_time
                        )
                        
                        # Generate content hash for deduplication
                        content = f"{game.id}|{bookmaker_key}|{market_type}|{outcome['name']}|{outcome.get('point')}|{outcome.get('price')}"
                        snapshot.content_hash = hashlib.md5(content.encode()).hexdigest()
                        
                        snapshots.append(snapshot)
            
            results.append((game, snapshots))
        
        return results
    
    async def upsert(self, normalized_data: List[Any]) -> Dict[str, int]:
        """
        Upsert games and odds snapshots.
        
        Args:
            normalized_data: List of (Game, List[OddsSnapshot]) tuples
        """
        games_inserted = 0
        snapshots_inserted = 0
        errors = 0
        
        for game, snapshots in normalized_data:
            try:
                # Upsert game
                game_dict = game.model_dump(exclude_none=True)
                self.db.table("games").upsert(game_dict, on_conflict="id").execute()
                games_inserted += 1
                
                # Store snapshots (with deduplication via CLV service)
                for snapshot in snapshots:
                    stored = await self.clv_service.store_odds_snapshot(
                        game_id=snapshot.game_id,
                        bookmaker_key=snapshot.bookmaker_key,
                        bookmaker_title=snapshot.bookmaker_title,
                        market_type=snapshot.market_type,
                        outcome_name=snapshot.outcome_name,
                        team=snapshot.team,
                        point=snapshot.point,
                        price=snapshot.price,
                        snapshot_time=snapshot.ts,
                        content_hash=snapshot.content_hash
                    )
                    if stored:
                        snapshots_inserted += 1
                
            except Exception as e:
                self.logger.error(f"Error upserting game {game.id}: {str(e)}")
                errors += 1
        
        return {
            "inserted": games_inserted + snapshots_inserted,
            "updated": 0,
            "errors": errors
        }
    
    async def healthcheck(self) -> Dict[str, Any]:
        """Check Odds API health."""
        try:
            # Check if API key is configured
            if not self.api_key:
                return {
                    "healthy": False,
                    "message": "Odds API key not configured",
                    "details": {}
                }
            
            # Check budget
            budget_check = await self.budget_service.check_budget("odds_api")
            
            if not budget_check["allowed"]:
                return {
                    "healthy": False,
                    "message": f"Budget exceeded: {budget_check['calls_made']}/{budget_check['calls_limit']}",
                    "details": budget_check
                }
            
            return {
                "healthy": True,
                "message": "Odds API ready",
                "details": {
                    "calls_remaining": budget_check["remaining"],
                    "calls_limit": budget_check["calls_limit"]
                }
            }
        
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Odds API error: {str(e)}",
                "details": {}
            }
    
    async def should_fetch_odds(self) -> bool:
        """
        Determine if we should fetch odds now based on:
        - Budget availability
        - Last fetch time
        - Game schedule
        """
        # Check budget
        if not await self._can_fetch_odds():
            return False
        
        # Check when we last fetched
        result = self.db.table("api_budget").select("last_call_at").eq("provider", "odds_api").eq("date", str(date.today())).execute()
        
        if result.data and len(result.data) > 0:
            last_call = result.data[0].get("last_call_at")
            if last_call:
                last_call_dt = datetime.fromisoformat(last_call.replace("Z", "+00:00"))
                hours_since_last = (datetime.utcnow() - last_call_dt.replace(tzinfo=None)).total_seconds() / 3600
                
                # Default: fetch every 12 hours
                fetch_interval = settings.odds_fetch_interval_hours
                
                # Check if there are games today - if so, might fetch more frequently
                today_games = self.db.table("games").select("id").gte("commence_time", datetime.utcnow().isoformat()).lte("commence_time", (datetime.utcnow() + timedelta(days=1)).isoformat()).execute()
                
                if today_games.data and len(today_games.data) > 0:
                    # Games today - can fetch every 6 hours if within budget
                    fetch_interval = 6
                
                if hours_since_last < fetch_interval:
                    logger.info(f"Skipping odds fetch - last fetch was {hours_since_last:.1f}h ago")
                    return False
        
        return True
