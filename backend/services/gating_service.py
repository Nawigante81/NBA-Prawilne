"""
NBA Betting Analytics Backend - Quality Gating Service
Implements quality gates to filter out poor betting opportunities
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from backend.db import fetch_one, fetch_all
from backend.models import ValueBet
from backend.settings import (
    MIN_EV,
    MIN_EDGE_PROB,
    ODDS_STALE_HOURS,
    STATS_MAX_AGE_HOURS,
    MIN_GAMES_RECENT,
    MIN_PLAYER_GAMES_RECENT,
    MIN_LIQUIDITY_SAMPLES
)

logger = logging.getLogger(__name__)


# Reason codes for quality gates
REASON_CODE_NO_ODDS_RECENT = "NO_ODDS_RECENT"
REASON_CODE_STATS_STALE = "STATS_STALE"
REASON_CODE_EV_TOO_LOW = "EV_TOO_LOW"
REASON_CODE_EDGE_TOO_LOW = "EDGE_TOO_LOW"
REASON_CODE_LOW_LIQUIDITY = "LOW_LIQUIDITY"
REASON_CODE_MISSING_COMMENCE_TIME = "MISSING_COMMENCE_TIME"
REASON_CODE_INSUFFICIENT_STATS = "INSUFFICIENT_STATS"
REASON_CODE_INSUFFICIENT_PLAYER_DATA = "INSUFFICIENT_PLAYER_DATA"


async def check_quality_gates(
    game_id: str,
    market_type: str,
    team: Optional[str],
    ev: float,
    edge_prob: float,
    model_prob: float,
    odds_timestamp: Optional[datetime],
    stats_timestamp: Optional[datetime],
    sample_count: Optional[int] = None
) -> Dict[str, Any]:
    """
    Check all quality gates for a betting opportunity.
    
    Args:
        game_id: Game identifier
        market_type: Market type (h2h, spread, totals)
        team: Team abbreviation (None for totals)
        ev: Expected value
        edge_prob: Edge probability
        model_prob: Model probability
        odds_timestamp: Timestamp of odds data
        stats_timestamp: Timestamp of stats data
        sample_count: Number of bookmaker samples for liquidity check
        
    Returns:
        Dict with:
            - passed (bool): Whether all gates passed
            - reason_codes (list): List of reason codes for failures/warnings
            - action (str): "BET" or "NO_BET"
    """
    reason_codes = []
    now = datetime.utcnow()
    
    # Check odds recency
    if odds_timestamp is None:
        reason_codes.append(REASON_CODE_NO_ODDS_RECENT)
    else:
        odds_age = now - odds_timestamp
        if odds_age > timedelta(hours=ODDS_STALE_HOURS):
            reason_codes.append(REASON_CODE_NO_ODDS_RECENT)
    
    # Check stats recency
    if stats_timestamp is None:
        reason_codes.append(REASON_CODE_STATS_STALE)
    else:
        stats_age = now - stats_timestamp
        if stats_age > timedelta(hours=STATS_MAX_AGE_HOURS):
            reason_codes.append(REASON_CODE_STATS_STALE)
    
    # Check minimum EV
    if ev < MIN_EV:
        reason_codes.append(REASON_CODE_EV_TOO_LOW)
    
    # Check minimum edge
    if edge_prob < MIN_EDGE_PROB:
        reason_codes.append(REASON_CODE_EDGE_TOO_LOW)
    
    # Check liquidity (warning only)
    if sample_count is not None and sample_count < MIN_LIQUIDITY_SAMPLES:
        reason_codes.append(REASON_CODE_LOW_LIQUIDITY)
    
    # Check commence_time exists in game
    game_query = "SELECT commence_time FROM games WHERE id = $1"
    game = await fetch_one(game_query, game_id)
    
    if game is None or game.get('commence_time') is None:
        reason_codes.append(REASON_CODE_MISSING_COMMENCE_TIME)
    
    # Determine if bet should be placed
    # LOW_LIQUIDITY is warning only, all others are blocking
    blocking_codes = [
        code for code in reason_codes 
        if code != REASON_CODE_LOW_LIQUIDITY
    ]
    
    passed = len(blocking_codes) == 0
    action = "BET" if passed else "NO_BET"
    
    return {
        "passed": passed,
        "reason_codes": reason_codes,
        "action": action
    }


async def check_stats_availability(game_id: str) -> Dict[str, Any]:
    """
    Check if sufficient stats exist for modeling.
    
    Args:
        game_id: Game identifier
        
    Returns:
        Dict with:
            - available (bool): Whether sufficient stats exist
            - reason_codes (list): List of reason codes
    """
    reason_codes = []
    
    # Get teams from game
    game_query = """
        SELECT home_team, away_team
        FROM games
        WHERE id = $1
    """
    game = await fetch_one(game_query, game_id)
    
    if not game:
        logger.warning(f"Game {game_id} not found")
        reason_codes.append(REASON_CODE_INSUFFICIENT_STATS)
        return {
            "available": False,
            "reason_codes": reason_codes
        }
    
    home_team = game.get('home_team')
    away_team = game.get('away_team')
    
    # Check stats for both teams
    for team in [home_team, away_team]:
        if not team:
            continue
            
        stats_query = """
            SELECT COUNT(*) as game_count
            FROM team_game_stats tgs
            JOIN games g ON tgs.game_id = g.id
            WHERE tgs.team_abbrev = $1
            AND g.status = 'final'
            ORDER BY g.commence_time DESC
            LIMIT $2
        """
        result = await fetch_one(stats_query, team, MIN_GAMES_RECENT)
        
        game_count = result.get('game_count', 0) if result else 0
        
        if game_count < MIN_GAMES_RECENT:
            reason_codes.append(REASON_CODE_INSUFFICIENT_STATS)
            break
    
    available = len(reason_codes) == 0
    
    return {
        "available": available,
        "reason_codes": reason_codes
    }


async def check_player_availability(team_abbrev: str) -> Dict[str, Any]:
    """
    Check key player availability for a team (simplified check).
    
    Args:
        team_abbrev: Team abbreviation
        
    Returns:
        Dict with:
            - available (bool): Whether sufficient player data exists
            - reason_codes (list): List of reason codes
    """
    reason_codes = []
    
    # Query for player game stats in last 3 games for this team
    # This is a simplified check - just verifying we have recent player data
    player_query = """
        SELECT COUNT(DISTINCT pgs.game_id) as game_count
        FROM player_game_stats pgs
        JOIN games g ON pgs.game_id = g.id
        WHERE pgs.team_abbrev = $1
        AND g.status = 'final'
        ORDER BY g.commence_time DESC
        LIMIT 3
    """
    result = await fetch_one(player_query, team_abbrev)
    
    game_count = result.get('game_count', 0) if result else 0
    
    if game_count < MIN_PLAYER_GAMES_RECENT:
        reason_codes.append(REASON_CODE_INSUFFICIENT_PLAYER_DATA)
    
    available = len(reason_codes) == 0
    
    return {
        "available": available,
        "reason_codes": reason_codes
    }


async def apply_gates_to_value_board(value_bets: List[ValueBet]) -> List[ValueBet]:
    """
    Apply quality gates to a list of ValueBet objects.
    
    Args:
        value_bets: List of ValueBet objects
        
    Returns:
        Filtered list of ValueBet objects that passed gates
    """
    filtered_bets = []
    
    for bet in value_bets:
        # Extract timestamps from metadata if available
        odds_timestamp = bet.metadata.get('odds_timestamp')
        stats_timestamp = bet.metadata.get('stats_timestamp')
        sample_count = bet.metadata.get('sample_count')
        
        # Check quality gates
        gate_result = await check_quality_gates(
            game_id=bet.game_id,
            market_type=bet.market.value,
            team=bet.team_abbrev,
            ev=bet.ev,
            edge_prob=bet.edge_prob,
            model_prob=bet.model_prob,
            odds_timestamp=odds_timestamp,
            stats_timestamp=stats_timestamp,
            sample_count=sample_count
        )
        
        # Add reason codes to bet
        bet.reason_codes.extend(gate_result['reason_codes'])
        
        # Only include bets with action="BET"
        if gate_result['action'] == "BET":
            filtered_bets.append(bet)
        else:
            logger.debug(
                f"Filtered out bet for game {bet.game_id}, market {bet.market}, "
                f"reasons: {gate_result['reason_codes']}"
            )
    
    logger.info(
        f"Quality gates: {len(value_bets)} input bets, "
        f"{len(filtered_bets)} passed gates"
    )
    
    return filtered_bets
