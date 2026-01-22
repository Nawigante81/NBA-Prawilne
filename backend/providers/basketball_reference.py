"""
Basketball-Reference scraper with polite rate limiting.
"""
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from providers.base import BaseProvider
from models import Team, Player
from settings import settings
import logging

logger = logging.getLogger(__name__)


class BasketballReferenceProvider(BaseProvider):
    """Provider for Basketball-Reference with polite scraping."""
    
    BASE_URL = "https://www.basketball-reference.com"
    
    def __init__(self, db_client):
        super().__init__(db_client)
        self._last_request_time = None
        self._lock = asyncio.Lock()
    
    async def _polite_request(self, url: str) -> str:
        """
        Make HTTP request with polite rate limiting.
        Enforces minimum 3 second interval between requests.
        """
        async with self._lock:
            # Enforce rate limit
            if self._last_request_time is not None:
                elapsed = (datetime.now() - self._last_request_time).total_seconds()
                wait_time = settings.basketball_ref_request_interval_seconds - elapsed
                if wait_time > 0:
                    logger.debug(f"Waiting {wait_time:.1f}s for rate limit")
                    await asyncio.sleep(wait_time)
            
            # Make request
            headers = {
                "User-Agent": "NBAAnalyticsBot/1.0 (Educational purposes; polite scraping)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 429:
                        logger.error("Basketball-Reference rate limit hit - stopping")
                        raise Exception("Rate limit hit - stopping scraping")
                    
                    if response.status_code != 200:
                        logger.error(f"Basketball-Reference returned {response.status_code}")
                        raise Exception(f"HTTP {response.status_code}")
                    
                    self._last_request_time = datetime.now()
                    return response.text
            
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise
    
    async def fetch_teams_page(self) -> str:
        """Fetch teams listing page."""
        url = f"{self.BASE_URL}/teams/"
        return await self._polite_request(url)
    
    async def fetch_roster_page(self, team_abbr: str, season: str = "2025") -> str:
        """Fetch team roster page."""
        url = f"{self.BASE_URL}/teams/{team_abbr}/{season}.html"
        return await self._polite_request(url)
    
    async def fetch(self, resource: str = "teams", **kwargs) -> Any:
        """
        Fetch data from Basketball-Reference.
        
        Args:
            resource: "teams" or "roster"
            **kwargs: Additional parameters (team_abbr, season for roster)
        """
        if resource == "teams":
            return await self.fetch_teams_page()
        elif resource == "roster":
            team_abbr = kwargs.get("team_abbr", "CHI")
            season = kwargs.get("season", "2025")
            return await self.fetch_roster_page(team_abbr, season)
        else:
            raise ValueError(f"Unknown resource: {resource}")
    
    def normalize(self, raw_data: Any) -> List[Any]:
        """Normalize Basketball-Reference HTML to models."""
        # This is resource-dependent
        # Actual normalization happens in parse methods
        return []
    
    def parse_teams(self, html: str) -> List[Team]:
        """Parse teams from HTML."""
        soup = BeautifulSoup(html, "lxml")
        teams = []
        
        try:
            # Find active teams table
            table = soup.find("table", {"id": "teams_active"})
            if not table:
                logger.warning("Could not find teams table")
                return teams
            
            rows = table.find("tbody").find_all("tr")
            
            for row in rows:
                if row.get("class") and "thead" in row.get("class"):
                    continue
                
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                
                team_link = cells[0].find("a")
                if not team_link:
                    continue
                
                full_name = team_link.text.strip()
                
                # Extract abbreviation from href
                href = team_link.get("href", "")
                abbr = href.split("/")[-2].upper() if "/" in href else "UNK"
                
                # Parse city and name
                parts = full_name.rsplit(" ", 1)
                if len(parts) == 2:
                    city, name = parts
                else:
                    city = ""
                    name = full_name
                
                team = Team(
                    abbreviation=abbr,
                    full_name=full_name,
                    name=name,
                    city=city
                )
                teams.append(team)
        
        except Exception as e:
            logger.error(f"Error parsing teams: {str(e)}")
        
        return teams
    
    def parse_roster(self, html: str, team_abbr: str) -> List[Player]:
        """Parse roster from HTML."""
        soup = BeautifulSoup(html, "lxml")
        players = []
        
        try:
            # Find roster table
            table = soup.find("table", {"id": "roster"})
            if not table:
                logger.warning("Could not find roster table")
                return players
            
            rows = table.find("tbody").find_all("tr")
            
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                
                # Player name
                name_cell = cells[0]
                name_link = name_cell.find("a")
                if not name_link:
                    continue
                
                name = name_link.text.strip()
                
                # Basketball-Reference ID
                href = name_link.get("href", "")
                bbref_id = href.split("/")[-1].replace(".html", "") if "/" in href else None
                
                # Jersey number
                jersey = None
                if len(cells) > 0:
                    try:
                        jersey = int(cells[0].text.strip())
                    except:
                        pass
                
                # Position
                position = cells[1].text.strip() if len(cells) > 1 else None
                
                player = Player(
                    name=name,
                    team_abbreviation=team_abbr,
                    jersey_number=jersey,
                    position=position,
                    basketball_reference_id=bbref_id,
                    basketball_reference_url=f"{self.BASE_URL}{href}" if href else None
                )
                players.append(player)
        
        except Exception as e:
            logger.error(f"Error parsing roster: {str(e)}")
        
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
        """Check Basketball-Reference availability."""
        try:
            # Try a simple request to the homepage
            html = await self._polite_request(self.BASE_URL)
            return {
                "healthy": True,
                "message": "Basketball-Reference accessible",
                "details": {"response_length": len(html)}
            }
        except Exception as e:
            return {
                "healthy": False,
                "message": f"Basketball-Reference error: {str(e)}",
                "details": {}
            }
