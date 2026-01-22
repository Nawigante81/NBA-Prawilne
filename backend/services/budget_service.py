"""
Budget service for tracking and enforcing API call limits.
"""
from datetime import date, datetime, timedelta
from typing import Optional, Dict
from db import get_db
from settings import settings
import logging

logger = logging.getLogger(__name__)


class BudgetService:
    """Service for managing API call budgets."""
    
    def __init__(self):
        self.db = get_db()
    
    async def check_budget(self, provider: str, date_val: Optional[date] = None) -> Dict[str, any]:
        """
        Check if provider has budget remaining for today.
        
        Args:
            provider: Provider name ("odds_api", "nba_api", "basketball_reference")
            date_val: Date to check (default: today)
        
        Returns:
            Dictionary with budget info: {"allowed": bool, "calls_made": int, "calls_limit": int, "remaining": int}
        """
        if date_val is None:
            date_val = date.today()
        
        # Get limit for provider
        limits = {
            "odds_api": settings.odds_max_calls_per_day,
            "nba_api": 1000,  # Generous limit, mainly controlled by TTL
            "basketball_reference": 100  # Polite scraping limit
        }
        
        limit = limits.get(provider, 100)
        
        # Query current usage
        result = self.db.table("api_budget").select("*").eq("provider", provider).eq("date", str(date_val)).execute()
        
        if result.data and len(result.data) > 0:
            entry = result.data[0]
            calls_made = entry.get("calls_made", 0)
        else:
            calls_made = 0
        
        remaining = limit - calls_made
        allowed = remaining > 0
        
        return {
            "allowed": allowed,
            "calls_made": calls_made,
            "calls_limit": limit,
            "remaining": remaining
        }
    
    async def increment_calls(self, provider: str, count: int = 1, date_val: Optional[date] = None) -> bool:
        """
        Increment call count for provider.
        
        Args:
            provider: Provider name
            count: Number of calls to add (default 1)
            date_val: Date to increment (default: today)
        
        Returns:
            True if increment successful, False if budget exceeded
        """
        if date_val is None:
            date_val = date.today()
        
        # Check budget first
        budget_check = await self.check_budget(provider, date_val)
        if not budget_check["allowed"]:
            logger.warning(f"Budget exceeded for {provider} on {date_val}")
            return False
        
        # Get current entry
        result = self.db.table("api_budget").select("*").eq("provider", provider).eq("date", str(date_val)).execute()
        
        now = datetime.utcnow().isoformat()
        
        if result.data and len(result.data) > 0:
            # Update existing
            entry = result.data[0]
            new_count = entry.get("calls_made", 0) + count
            
            self.db.table("api_budget").update({
                "calls_made": new_count,
                "last_call_at": now
            }).eq("id", entry["id"]).execute()
            
            logger.info(f"Incremented {provider} calls to {new_count} on {date_val}")
        else:
            # Create new entry
            limits = {
                "odds_api": settings.odds_max_calls_per_day,
                "nba_api": 1000,
                "basketball_reference": 100
            }
            limit = limits.get(provider, 100)
            
            self.db.table("api_budget").insert({
                "provider": provider,
                "date": str(date_val),
                "calls_made": count,
                "calls_limit": limit,
                "last_call_at": now
            }).execute()
            
            logger.info(f"Created budget entry for {provider} on {date_val} with {count} calls")
        
        return True
    
    async def get_budget_summary(self, date_val: Optional[date] = None) -> Dict[str, Dict]:
        """
        Get budget summary for all providers.
        
        Args:
            date_val: Date to check (default: today)
        
        Returns:
            Dictionary mapping provider -> budget info
        """
        if date_val is None:
            date_val = date.today()
        
        providers = ["odds_api", "nba_api", "basketball_reference"]
        summary = {}
        
        for provider in providers:
            summary[provider] = await self.check_budget(provider, date_val)
        
        return summary
    
    async def reset_budget(self, provider: str, date_val: Optional[date] = None) -> bool:
        """
        Reset budget for a provider (admin function).
        
        Args:
            provider: Provider name
            date_val: Date to reset (default: today)
        
        Returns:
            True if successful
        """
        if date_val is None:
            date_val = date.today()
        
        result = self.db.table("api_budget").delete().eq("provider", provider).eq("date", str(date_val)).execute()
        
        logger.info(f"Reset budget for {provider} on {date_val}")
        return True


# Global instance
_budget_service: Optional[BudgetService] = None


def get_budget_service() -> BudgetService:
    """Get or create budget service singleton."""
    global _budget_service
    if _budget_service is None:
        _budget_service = BudgetService()
    return _budget_service
