"""
Base provider interface that all data providers must implement.
"""
from abc import ABC, abstractmethod
from typing import List, Any, Dict
from models import Team, Player, Game, TeamGameStat, PlayerGameStat, OddsSnapshot
import logging

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for all data providers.
    Each provider must implement fetch, normalize, upsert, and healthcheck methods.
    """
    
    def __init__(self, db_client):
        """
        Initialize provider with database client.
        
        Args:
            db_client: Supabase client for database operations
        """
        self.db = db_client
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def fetch(self, **kwargs) -> Any:
        """
        Fetch raw data from the provider source.
        
        Returns:
            Raw data from the source (format depends on provider)
        """
        pass
    
    @abstractmethod
    def normalize(self, raw_data: Any) -> List[Any]:
        """
        Normalize raw data into Pydantic models.
        
        Args:
            raw_data: Raw data fetched from source
            
        Returns:
            List of normalized Pydantic models (Team, Player, Game, etc.)
        """
        pass
    
    @abstractmethod
    async def upsert(self, normalized_data: List[Any]) -> Dict[str, int]:
        """
        Insert or update normalized data in the database.
        
        Args:
            normalized_data: List of Pydantic models
            
        Returns:
            Dictionary with counts: {"inserted": n, "updated": m, "errors": k}
        """
        pass
    
    @abstractmethod
    async def healthcheck(self) -> Dict[str, Any]:
        """
        Check if provider is healthy and accessible.
        
        Returns:
            Dictionary with status and details:
            {
                "healthy": bool,
                "message": str,
                "details": dict
            }
        """
        pass
    
    async def sync(self, **kwargs) -> Dict[str, Any]:
        """
        Complete sync operation: fetch -> normalize -> upsert.
        
        Returns:
            Dictionary with sync results
        """
        try:
            self.logger.info(f"Starting sync for {self.__class__.__name__}")
            
            # Fetch raw data
            raw_data = await self.fetch(**kwargs)
            
            # Normalize to models
            normalized = self.normalize(raw_data)
            self.logger.info(f"Normalized {len(normalized)} items")
            
            # Upsert to database
            result = await self.upsert(normalized)
            self.logger.info(f"Upsert complete: {result}")
            
            return {
                "success": True,
                "provider": self.__class__.__name__,
                "items_processed": len(normalized),
                "upsert_result": result
            }
            
        except Exception as e:
            self.logger.error(f"Sync failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "provider": self.__class__.__name__,
                "error": str(e)
            }
