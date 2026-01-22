"""
Quality gate system for betting recommendations.
Ensures minimum data quality criteria are met before generating picks.
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from statistics import stdev
from db import get_db
from models import QualityGateResult, GateFailureReason
from settings import settings
import logging

logger = logging.getLogger(__name__)


class QualityGateService:
    """Service for enforcing quality gates on betting recommendations."""
    
    def __init__(self):
        self.db = get_db()
        self.settings = settings
    
    async def check_odds_availability(self, game_id: str, market_type: str) -> QualityGateResult:
        """
        Check if odds data is available and recent enough.
        
        Criteria:
        - At least 1 bookmaker snapshot within last 12h OR last snapshot before game start
        - Odds must have current line + price
        """
        reasons = []
        details = {}
        
        # Get game commence time
        game_result = self.db.table("games").select("commence_time").eq("id", game_id).execute()
        
        if not game_result.data or len(game_result.data) == 0:
            reasons.append(GateFailureReason.MISSING_COMMENCE_TIME)
            return QualityGateResult(passed=False, reasons=reasons, details={"error": "Game not found"})
        
        commence_time = datetime.fromisoformat(game_result.data[0]["commence_time"].replace("Z", "+00:00"))
        now = datetime.utcnow()
        
        # Check for recent odds
        cutoff_time = now - timedelta(hours=self.settings.odds_max_snapshot_age_hours)
        
        odds_result = self.db.table("odds_snapshots").select("*").eq("game_id", game_id).eq("market_type", market_type).gte("snapshot_time", cutoff_time.isoformat()).execute()
        
        if not odds_result.data or len(odds_result.data) == 0:
            # No recent odds - check if we have pre-game odds
            if now < commence_time:
                reasons.append(GateFailureReason.NO_ODDS_RECENT)
                details["last_odds_age_hours"] = "N/A"
            else:
                # Game already started - need closing line
                closing_result = self.db.table("odds_snapshots").select("*").eq("game_id", game_id).eq("market_type", market_type).lt("snapshot_time", commence_time.isoformat()).order("snapshot_time", desc=True).limit(1).execute()
                
                if not closing_result.data:
                    reasons.append(GateFailureReason.MISSING_CLOSING_LINE)
        
        else:
            # Check data quality
            latest_snapshot = odds_result.data[0]
            if latest_snapshot.get("price") is None:
                reasons.append(GateFailureReason.NO_ODDS_RECENT)
                details["missing_price"] = True
            
            if market_type in ["spreads", "totals"] and latest_snapshot.get("point") is None:
                reasons.append(GateFailureReason.NO_ODDS_RECENT)
                details["missing_point"] = True
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_team_sample_size(self, team_abbr: str, min_games: Optional[int] = None) -> QualityGateResult:
        """
        Check if team has sufficient recent game data.
        
        Criteria:
        - At least N=5 games of recent stats (last-5) OR fallback to last-10
        - If less than 5 games available -> analysis allowed, but no picks
        """
        if min_games is None:
            min_games = self.settings.min_games_recent
        
        reasons = []
        details = {}
        
        # Query recent team game stats
        result = self.db.table("team_game_stats").select("*").eq("team_abbreviation", team_abbr).order("game_date", desc=True).limit(10).execute()
        
        games_count = len(result.data) if result.data else 0
        details["games_available"] = games_count
        
        if games_count < min_games:
            reasons.append(GateFailureReason.INSUFFICIENT_SAMPLE)
            details["required_games"] = min_games
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_player_sample_size(self, player_id: str, min_games: Optional[int] = None) -> QualityGateResult:
        """
        Check if player has sufficient recent game data.
        
        Criteria:
        - Must have player minutes in last 5 games
        - At least 3 games played in that window
        - If minutes data missing or player DNP/uncertain -> no player prop picks
        """
        if min_games is None:
            min_games = self.settings.min_player_games_recent
        
        reasons = []
        details = {}
        
        # Query recent player game stats
        result = self.db.table("player_game_stats").select("*").eq("player_id", player_id).order("game_date", desc=True).limit(5).execute()
        
        games_count = len(result.data) if result.data else 0
        details["games_available"] = games_count
        
        if games_count < min_games:
            reasons.append(GateFailureReason.INSUFFICIENT_SAMPLE)
            details["required_games"] = min_games
            return QualityGateResult(passed=False, reasons=reasons, details=details)
        
        # Check for minutes data
        games_with_minutes = 0
        for game in result.data:
            if game.get("minutes") is not None and game.get("minutes") > 0:
                games_with_minutes += 1
        
        details["games_with_minutes"] = games_with_minutes
        
        if games_with_minutes < min_games:
            reasons.append(GateFailureReason.PLAYER_MINUTES_UNKNOWN)
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_stats_recency(self, team_abbr: str) -> QualityGateResult:
        """
        Check if stats are recent enough.
        
        Criteria:
        - Last update of stats must be < 24h
        """
        reasons = []
        details = {}
        
        # Get most recent team game stat
        result = self.db.table("team_game_stats").select("created_at").eq("team_abbreviation", team_abbr).order("created_at", desc=True).limit(1).execute()
        
        if not result.data or len(result.data) == 0:
            reasons.append(GateFailureReason.STATS_TOO_OLD)
            details["last_update"] = None
            return QualityGateResult(passed=False, reasons=reasons, details=details)
        
        last_update = datetime.fromisoformat(result.data[0]["created_at"].replace("Z", "+00:00"))
        hours_since_update = (datetime.utcnow() - last_update.replace(tzinfo=None)).total_seconds() / 3600
        
        details["hours_since_update"] = hours_since_update
        
        if hours_since_update > self.settings.stats_max_age_hours:
            reasons.append(GateFailureReason.STATS_TOO_OLD)
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_market_quality(self, odds: float, odds_format: str = "american") -> QualityGateResult:
        """
        Check if market has acceptable juice.
        
        Criteria:
        - Reject markets with extreme juice (worse than -160 American odds)
        """
        reasons = []
        details = {"odds": odds, "odds_format": odds_format}
        
        if odds_format == "american":
            # Check if favorite odds are too juicy
            if odds < self.settings.odds_max_american_favorite:
                reasons.append(GateFailureReason.HIGH_JUICE)
                details["threshold"] = self.settings.odds_max_american_favorite
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_ev_threshold(self, ev: float, edge: float, confidence: float) -> QualityGateResult:
        """
        Check if pick meets EV and edge thresholds.
        
        Criteria:
        - EV >= MIN_EV (default 2%)
        - Edge >= MIN_EDGE_PROB (default 3 percentage points)
        - Confidence >= MIN_CONFIDENCE (default 0.55)
        """
        reasons = []
        details = {"ev": ev, "edge": edge, "confidence": confidence}
        
        if ev < self.settings.min_ev:
            reasons.append(GateFailureReason.EV_TOO_LOW)
            details["min_ev"] = self.settings.min_ev
        
        if edge < self.settings.min_edge_prob:
            reasons.append(GateFailureReason.EDGE_TOO_SMALL)
            details["min_edge"] = self.settings.min_edge_prob
        
        if confidence < self.settings.min_confidence:
            reasons.append(GateFailureReason.CONFIDENCE_TOO_LOW)
            details["min_confidence"] = self.settings.min_confidence
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_parlay_quality(self, legs: List[Dict], combined_implied_prob: float) -> QualityGateResult:
        """
        Check if parlay meets quality criteria.
        
        Criteria:
        - Max legs: 5
        - Each leg must pass single-pick gates
        - Combined implied probability >= 0.20 for "low-risk" parlays
        """
        reasons = []
        details = {"num_legs": len(legs), "combined_implied_prob": combined_implied_prob}
        
        if len(legs) > self.settings.parlay_max_legs:
            reasons.append(GateFailureReason.HIGH_JUICE)  # Using this as proxy for "too many legs"
            details["max_legs"] = self.settings.parlay_max_legs
        
        if combined_implied_prob < self.settings.parlay_min_combined_implied_prob:
            reasons.append(GateFailureReason.EV_TOO_LOW)
            details["min_combined_prob"] = self.settings.parlay_min_combined_implied_prob
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_minutes_volatility(self, player_id: str) -> QualityGateResult:
        """
        Check player minutes volatility as uncertainty flag.
        
        Criteria:
        - If top-3 usage players have minutes stddev > threshold -> volatility risk
        """
        reasons = []
        details = {}
        
        # Get last 5 games minutes
        result = self.db.table("player_game_stats").select("minutes").eq("player_id", player_id).order("game_date", desc=True).limit(5).execute()
        
        if not result.data or len(result.data) < 3:
            reasons.append(GateFailureReason.PLAYER_MINUTES_UNKNOWN)
            return QualityGateResult(passed=False, reasons=reasons, details=details)
        
        minutes_list = [g["minutes"] for g in result.data if g.get("minutes") is not None]
        
        if len(minutes_list) < 3:
            reasons.append(GateFailureReason.PLAYER_MINUTES_UNKNOWN)
            return QualityGateResult(passed=False, reasons=reasons, details=details)
        
        minutes_stddev = stdev(minutes_list) if len(minutes_list) > 1 else 0
        avg_minutes = sum(minutes_list) / len(minutes_list)
        
        details["minutes_stddev"] = minutes_stddev
        details["avg_minutes"] = avg_minutes
        
        # High volatility if stddev > 8 minutes
        if minutes_stddev > 8.0:
            reasons.append(GateFailureReason.PLAYER_MINUTES_UNKNOWN)
            details["high_volatility"] = True
        
        passed = len(reasons) == 0
        return QualityGateResult(passed=passed, reasons=reasons, details=details)
    
    async def check_all_gates_for_game(self, game_id: str, market_type: str, team_abbr: str) -> QualityGateResult:
        """
        Run all relevant quality gates for a game pick.
        
        Returns:
            Aggregate gate result
        """
        all_reasons = []
        all_details = {}
        
        # Check odds availability
        odds_gate = await self.check_odds_availability(game_id, market_type)
        if not odds_gate.passed:
            all_reasons.extend(odds_gate.reasons)
            all_details["odds"] = odds_gate.details
        
        # Check team sample size
        team_gate = await self.check_team_sample_size(team_abbr)
        if not team_gate.passed:
            all_reasons.extend(team_gate.reasons)
            all_details["team_sample"] = team_gate.details
        
        # Check stats recency
        recency_gate = await self.check_stats_recency(team_abbr)
        if not recency_gate.passed:
            all_reasons.extend(recency_gate.reasons)
            all_details["stats_recency"] = recency_gate.details
        
        passed = len(all_reasons) == 0
        return QualityGateResult(passed=passed, reasons=all_reasons, details=all_details)


# Global instance
_quality_gate_service: Optional[QualityGateService] = None


def get_quality_gate_service() -> QualityGateService:
    """Get or create quality gate service singleton."""
    global _quality_gate_service
    if _quality_gate_service is None:
        _quality_gate_service = QualityGateService()
    return _quality_gate_service
