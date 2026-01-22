"""
Database connection and utilities.
"""
import os
from typing import Optional
from supabase import create_client, Client
from settings import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Singleton Supabase client."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._instance is None:
            if not settings.supabase_url or not settings.supabase_service_role_key:
                raise ValueError("Supabase credentials not configured")
            
            cls._instance = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            logger.info("Supabase client initialized")
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset client (useful for testing)."""
        cls._instance = None


def get_db() -> Client:
    """Get database client."""
    return DatabaseClient.get_client()
