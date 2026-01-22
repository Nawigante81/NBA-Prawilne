"""
NBA Betting Analytics Backend - Database Layer
Database connection and helper functions
"""
import asyncpg
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import hashlib
import json

from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

# ==================================================================
# DATABASE CONNECTION POOL
# ==================================================================
_pool: Optional[asyncpg.Pool] = None


def get_db_connection_string() -> str:
    """Extract database connection string from Supabase URL"""
    # Supabase URL format: https://[project-ref].supabase.co
    # Postgres connection: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
    
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL not set")
    
    # Extract project ref from URL
    project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "").split("/")[0]
    
    # Build connection string using service key as password
    db_url = f"postgresql://postgres.{project_ref}:{SUPABASE_SERVICE_KEY}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    return db_url


async def init_db_pool():
    """Initialize database connection pool"""
    global _pool
    
    if _pool is not None:
        return _pool
    
    try:
        db_url = get_db_connection_string()
        _pool = await asyncpg.create_pool(
            db_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info("Database pool initialized successfully")
        return _pool
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


async def close_db_pool():
    """Close database connection pool"""
    global _pool
    
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database pool closed")


async def get_db() -> asyncpg.Pool:
    """Get database pool"""
    global _pool
    
    if _pool is None:
        await init_db_pool()
    
    return _pool


# ==================================================================
# HELPER FUNCTIONS
# ==================================================================

async def execute_query(query: str, *args) -> str:
    """Execute a query and return status"""
    pool = await get_db()
    async with pool.acquire() as conn:
        result = await conn.execute(query, *args)
        return result


async def fetch_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """Fetch a single row"""
    pool = await get_db()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_all(query: str, *args) -> List[Dict[str, Any]]:
    """Fetch all rows"""
    pool = await get_db()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_val(query: str, *args) -> Any:
    """Fetch a single value"""
    pool = await get_db()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)


def generate_content_hash(data: Dict[str, Any]) -> str:
    """Generate a content hash for deduplication"""
    # Create a stable JSON representation
    stable_json = json.dumps(data, sort_keys=True)
    return hashlib.sha256(stable_json.encode()).hexdigest()


# ==================================================================
# API BUDGET FUNCTIONS
# ==================================================================

async def check_api_budget(provider: str, max_calls: int) -> bool:
    """Check if API budget allows another call"""
    today = date.today()
    
    query = """
        SELECT calls 
        FROM api_budget 
        WHERE provider = $1 AND day = $2
    """
    
    result = await fetch_val(query, provider, today)
    current_calls = result if result is not None else 0
    
    return current_calls < max_calls


async def increment_api_budget(provider: str):
    """Increment API call counter"""
    today = date.today()
    
    query = """
        INSERT INTO api_budget (provider, day, calls)
        VALUES ($1, $2, 1)
        ON CONFLICT (provider, day) 
        DO UPDATE SET calls = api_budget.calls + 1
    """
    
    await execute_query(query, provider, today)
    logger.info(f"Incremented {provider} API budget for {today}")


async def get_api_budget_status(provider: str) -> Dict[str, Any]:
    """Get current API budget status"""
    today = date.today()
    
    query = """
        SELECT calls 
        FROM api_budget 
        WHERE provider = $1 AND day = $2
    """
    
    result = await fetch_val(query, provider, today)
    calls = result if result is not None else 0
    
    return {
        "provider": provider,
        "day": today.isoformat(),
        "calls_used": calls
    }


# ==================================================================
# CACHE FUNCTIONS
# ==================================================================

async def get_cache(provider: str, cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached data if not expired"""
    query = """
        SELECT payload, created_at, ttl_seconds
        FROM api_cache
        WHERE provider = $1 AND cache_key = $2
        ORDER BY created_at DESC
        LIMIT 1
    """
    
    result = await fetch_one(query, provider, cache_key)
    
    if not result:
        return None
    
    # Check if expired
    age_seconds = (datetime.now() - result['created_at']).total_seconds()
    if age_seconds > result['ttl_seconds']:
        return None
    
    return result['payload']


async def set_cache(provider: str, cache_key: str, payload: Dict[str, Any], ttl_seconds: int):
    """Set cache entry"""
    query = """
        INSERT INTO api_cache (provider, cache_key, payload, ttl_seconds)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (provider, cache_key)
        DO UPDATE SET 
            payload = EXCLUDED.payload,
            created_at = now(),
            ttl_seconds = EXCLUDED.ttl_seconds
    """
    
    await execute_query(query, provider, cache_key, json.dumps(payload), ttl_seconds)


async def clear_expired_cache():
    """Clear expired cache entries"""
    query = """
        DELETE FROM api_cache
        WHERE created_at + (ttl_seconds || ' seconds')::interval < now()
    """
    
    result = await execute_query(query)
    logger.info(f"Cleared expired cache entries: {result}")
