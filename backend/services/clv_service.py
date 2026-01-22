"""
NBA Betting Analytics Backend - CLV Service
Tracks and calculates Closing Line Value (CLV) for picks
"""
import logging
from typing import Dict, Optional, Any

from db import fetch_one, fetch_all
from services.odds_service import get_consensus_line

logger = logging.getLogger(__name__)


async def compute_closing_line(
    game_id: str,
    market_type: str,
    team: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Compute and store consensus closing line
    
    Args:
        game_id: Game identifier
        market_type: Market type ('spread', 'totals', 'h2h')
        team: Team abbreviation (required for spread/h2h)
    
    Returns:
        ConsensusLine dict or None if error
    """
    try:
        # Check if closing line already exists
        existing = await get_closing_line(game_id, market_type, team)
        if existing:
            logger.info(
                f"Closing line already exists for game={game_id}, "
                f"market={market_type}, team={team}"
            )
            return existing
        
        # Get game commence_time to use as cutoff
        game_query = """
            SELECT id, commence_time
            FROM games
            WHERE id = $1
        """
        game = await fetch_one(game_query, game_id)
        
        if not game:
            logger.warning(f"Game not found: {game_id}")
            return None
        
        cutoff_time = game["commence_time"]
        
        # Get consensus line from odds_service
        consensus = await get_consensus_line(
            game_id=game_id,
            market_type=market_type,
            team=team,
            cutoff_time=cutoff_time
        )
        
        if consensus["status"] != "success":
            logger.warning(
                f"Failed to compute consensus line for game={game_id}, "
                f"market={market_type}, team={team}: {consensus['status']}"
            )
            return None
        
        # Store closing line in database
        insert_query = """
            INSERT INTO closing_lines (
                game_id, market_type, team, point, price, ts_cutoff,
                method, sample_count, used_bookmakers
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (game_id, market_type, COALESCE(team, ''))
            DO NOTHING
            RETURNING *
        """
        
        result = await fetch_one(
            insert_query,
            game_id,
            market_type,
            team,
            consensus["consensus_point"],
            consensus["consensus_price"],
            cutoff_time,
            "consensus_median_mad",
            consensus["sample_count"],
            consensus["used_bookmakers"]
        )
        
        if result:
            logger.info(
                f"Stored closing line for game={game_id}, market={market_type}, "
                f"team={team}, point={consensus['consensus_point']}, "
                f"price={consensus['consensus_price']}"
            )
        
        return consensus
        
    except Exception as e:
        logger.error(
            f"Error computing closing line for game={game_id}, "
            f"market={market_type}, team={team}: {e}"
        )
        return None


async def get_closing_line(
    game_id: str,
    market_type: str,
    team: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get existing closing line from database
    
    Args:
        game_id: Game identifier
        market_type: Market type ('spread', 'totals', 'h2h')
        team: Team abbreviation (optional)
    
    Returns:
        Closing line dict or None if not found
    """
    try:
        query = """
            SELECT *
            FROM closing_lines
            WHERE game_id = $1
              AND market_type = $2
              AND COALESCE(team, '') = COALESCE($3, '')
        """
        
        result = await fetch_one(query, game_id, market_type, team)
        return result
        
    except Exception as e:
        logger.error(
            f"Error fetching closing line for game={game_id}, "
            f"market={market_type}, team={team}: {e}"
        )
        return None


async def compute_clv_for_pick(pick_id: str) -> Optional[Dict[str, float]]:
    """
    Calculate CLV for a settled pick
    
    Args:
        pick_id: Pick identifier (UUID)
    
    Returns:
        Dict with clv_points and clv_percentage, or None if cannot compute
    """
    try:
        # Get pick details
        pick_query = """
            SELECT 
                id, game_id, team_abbrev, market, 
                line, price, status
            FROM picks
            WHERE id = $1
        """
        pick = await fetch_one(pick_query, pick_id)
        
        if not pick:
            logger.warning(f"Pick not found: {pick_id}")
            return None
        
        # Get closing line for same game/market/team
        closing_line = await get_closing_line(
            game_id=pick["game_id"],
            market_type=pick["market"],
            team=pick["team_abbrev"]
        )
        
        if not closing_line:
            logger.warning(
                f"No closing line found for pick={pick_id}, "
                f"game={pick['game_id']}, market={pick['market']}, "
                f"team={pick['team_abbrev']}"
            )
            return None
        
        # Calculate CLV based on market type
        clv_points = None
        clv_percentage = None
        
        if pick["market"] in ["spread", "totals"]:
            # For spread/totals: CLV is points difference
            if pick["line"] is not None and closing_line["point"] is not None:
                pick_line = float(pick["line"])
                closing_point = float(closing_line["point"])
                
                # CLV points: difference between closing line and pick line
                # Positive CLV means we got a better line than closing
                if pick["market"] == "spread":
                    # For spread, better line is more favorable
                    # If we bet favorite (-7) and closing is (-7.5), we got better line (+0.5 CLV)
                    clv_points = closing_point - pick_line
                else:
                    # For totals, use absolute difference
                    # Note: This is simplified - ideally should track over/under selection
                    # to determine if positive CLV means better or worse line
                    clv_points = abs(closing_point - pick_line)
        
        if pick["market"] == "h2h":
            # For h2h: CLV is odds difference
            if pick["price"] is not None and closing_line["price"] is not None:
                pick_price = float(pick["price"])
                closing_price = float(closing_line["price"])
                
                # CLV percentage: (closing_odds - pick_odds) / pick_odds
                clv_percentage = ((closing_price - pick_price) / pick_price) * 100
        
        # Calculate percentage CLV from points for spread/totals
        if clv_points is not None and pick["line"] is not None:
            pick_line = float(pick["line"])
            if pick_line != 0:
                clv_percentage = (clv_points / abs(pick_line)) * 100
            else:
                clv_percentage = 0.0
        
        result = {
            "clv_points": clv_points,
            "clv_percentage": clv_percentage
        }
        
        logger.info(
            f"Computed CLV for pick={pick_id}: "
            f"points={clv_points}, percentage={clv_percentage}%"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error computing CLV for pick={pick_id}: {e}")
        return None


async def compute_all_closing_lines() -> int:
    """
    Batch compute closing lines for all finished games
    
    Returns:
        Count of closing lines computed
    """
    try:
        # Find games that are finished and in the past
        games_query = """
            SELECT id, commence_time, home_team, away_team
            FROM games
            WHERE status = 'final'
              AND commence_time < NOW()
            ORDER BY commence_time DESC
        """
        
        games = await fetch_all(games_query)
        
        if not games:
            logger.info("No finished games found")
            return 0
        
        logger.info(f"Found {len(games)} finished games to process")
        
        lines_computed = 0
        markets = ["spread", "totals", "h2h"]
        
        for game in games:
            game_id = game["id"]
            home_team = game["home_team"]
            away_team = game["away_team"]
            
            # Compute closing lines for each market
            for market_type in markets:
                if market_type == "spread":
                    # Spread: compute for both teams
                    for team in [home_team, away_team]:
                        result = await compute_closing_line(game_id, market_type, team)
                        # Result is either existing DB record, new consensus dict, or None
                        if result is not None:
                            lines_computed += 1
                
                elif market_type == "totals":
                    # Totals: one line per game (no team)
                    result = await compute_closing_line(game_id, market_type, None)
                    if result is not None:
                        lines_computed += 1
                
                elif market_type == "h2h":
                    # H2H: compute for both teams
                    for team in [home_team, away_team]:
                        result = await compute_closing_line(game_id, market_type, team)
                        if result is not None:
                            lines_computed += 1
        
        logger.info(
            f"Computed {lines_computed} closing lines for {len(games)} games"
        )
        
        return lines_computed
        
    except Exception as e:
        logger.error(f"Error computing all closing lines: {e}")
        return 0
