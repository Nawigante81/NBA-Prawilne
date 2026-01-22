"""
Database connection and utilities.
"""
import os
from typing import Optional
from supabase import create_client, Client
from settings import settings
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Singleton Supabase client."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client."""
        if cls._instance is None:
            supabase_url = settings.supabase_url
            service_key = settings.supabase_service_role_key
            if not supabase_url or not service_key:
                backend_env = os.path.join(os.path.dirname(__file__), ".env")
                project_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
                load_dotenv(backend_env, override=False)
                load_dotenv(project_env, override=False)
                supabase_url = os.getenv("SUPABASE_URL", "") or os.getenv("VITE_SUPABASE_URL", "")
                service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

            if not supabase_url or not service_key:
                raise ValueError("Supabase credentials not configured")
            
            cls._instance = create_client(
                supabase_url,
                service_key
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
