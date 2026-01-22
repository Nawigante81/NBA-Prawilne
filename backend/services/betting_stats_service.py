"""
NBA Betting Analytics Backend - Betting Stats Service
Computes ATS (Against The Spread) and O/U (Over/Under) statistics using consensus closing lines
"""
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime

from backend.db import fetch_one, fetch_all, execute_query
from backend.services.odds_service import get_consensus_line

logger = logging.getLogger(__name__)


async def compute_ats_result(game_id: str, team_abbrev: str) -> Optional[str]:
    """
    Compute ATS result for a team in a game
    
    Args:
        game_id: Game identifier
        team_abbrev: Team abbreviation
        
    Returns:
        "win", "loss", "push", or None if cannot compute
    """
    try:
        # Get team's game result
        result_query = """
            SELECT points_for, points_against, is_home
            FROM team_game_results
            WHERE game_id = $1 AND team_abbrev = $2
        """
        team_result = await fetch_one(result_query, game_id, team_abbrev)
        
        if not team_result:
            logger.warning(f"No game result found for game_id={game_id}, team={team_abbrev}")
            return None
            
        # Get consensus closing spread from closing_lines table
        spread_query = """
            SELECT point, price
            FROM closing_lines
            WHERE game_id = $1 AND market_type = 'spread' AND team = $2
        """
        closing_spread = await fetch_one(spread_query, game_id, team_abbrev)
        
        if not closing_spread or closing_spread['point'] is None:
            logger.warning(f"No closing spread found for game_id={game_id}, team={team_abbrev}")
            return None
            
        # Calculate ATS result
        # Spread is negative for favorites (e.g., -7.5)
        # Team covers if: team_points + spread > opp_points
        points_for = team_result['points_for']
        points_against = team_result['points_against']
        spread = float(closing_spread['point'])
        
        adjusted_margin = points_for + spread - points_against
        
        if adjusted_margin > 0:
            return "win"
        elif adjusted_margin < 0:
            return "loss"
        else:
            return "push"
            
    except Exception as e:
        logger.error(f"Error computing ATS result for game_id={game_id}, team={team_abbrev}: {e}")
        return None


async def compute_ou_result(game_id: str) -> Optional[str]:
    """
    Compute O/U result for a game
    
    Args:
        game_id: Game identifier
        
    Returns:
        "over", "under", "push", or None if cannot compute
    """
    try:
        # Get both teams' scores from team_game_results
        results_query = """
            SELECT team_abbrev, points_for
            FROM team_game_results
            WHERE game_id = $1
        """
        results = await fetch_all(results_query, game_id)
        
        if len(results) != 2:
            logger.warning(f"Expected 2 team results for game_id={game_id}, found {len(results)}")
            return None
            
        # Calculate total points
        total_points = sum(r['points_for'] for r in results)
        
        # Get consensus closing total from closing_lines table
        total_query = """
            SELECT point, price
            FROM closing_lines
            WHERE game_id = $1 AND market_type = 'totals'
            LIMIT 1
        """
        closing_total = await fetch_one(total_query, game_id)
        
        if not closing_total or closing_total['point'] is None:
            logger.warning(f"No closing total found for game_id={game_id}")
            return None
            
        closing_line = float(closing_total['point'])
        
        if total_points > closing_line:
            return "over"
        elif total_points < closing_line:
            return "under"
        else:
            return "push"
            
    except Exception as e:
        logger.error(f"Error computing O/U result for game_id={game_id}: {e}")
        return None


async def get_team_ats_stats(team_abbrev: str, window: int = 20) -> Dict[str, Any]:
    """
    Get team ATS statistics over last N finished games
    
    Args:
        team_abbrev: Team abbreviation
        window: Number of recent games to analyze (default: 20)
        
    Returns:
        Dict with ATS statistics including win_pct, roi, record, games_analyzed
    """
    try:
        # Query last N finished games with results and closing lines
        query = """
            SELECT 
                tgr.game_id,
                tgr.points_for,
                tgr.points_against,
                cl.point as spread
            FROM team_game_results tgr
            JOIN games g ON tgr.game_id = g.id
            JOIN closing_lines cl ON tgr.game_id = cl.game_id 
                AND cl.market_type = 'spread' 
                AND cl.team = tgr.team_abbrev
            WHERE tgr.team_abbrev = $1
                AND g.status = 'final'
                AND cl.point IS NOT NULL
            ORDER BY g.commence_time DESC
            LIMIT $2
        """
        
        games = await fetch_all(query, team_abbrev, window)
        
        if not games:
            return {
                "team": team_abbrev,
                "games_analyzed": 0,
                "record": "0-0-0",
                "win_pct": 0.0,
                "roi": 0.0,
                "avg_spread_diff": 0.0
            }
            
        # Calculate ATS results
        wins = 0
        losses = 0
        pushes = 0
        spread_diffs = []
        
        for game in games:
            points_for = game['points_for']
            points_against = game['points_against']
            spread = float(game['spread'])
            
            actual_margin = points_for - points_against
            adjusted_margin = points_for + spread - points_against
            spread_diff = actual_margin - spread
            spread_diffs.append(spread_diff)
            
            if adjusted_margin > 0:
                wins += 1
            elif adjusted_margin < 0:
                losses += 1
            else:
                pushes += 1
                
        games_analyzed = len(games)
        decided_games = wins + losses
        
        # Calculate win percentage (excluding pushes)
        win_pct = (wins / decided_games) if decided_games > 0 else 0.0
        
        # Calculate ROI assuming -110 odds (risk $110 to win $100)
        # Wins pay +100/110 = 0.909, losses cost 1.0
        roi = ((wins * 0.909) - losses) / games_analyzed if games_analyzed > 0 else 0.0
        
        # Average spread differential
        avg_spread_diff = sum(spread_diffs) / len(spread_diffs) if spread_diffs else 0.0
        
        return {
            "team": team_abbrev,
            "games_analyzed": games_analyzed,
            "record": f"{wins}-{losses}-{pushes}",
            "win_pct": round(win_pct, 3),
            "roi": round(roi, 3),
            "avg_spread_diff": round(avg_spread_diff, 2)
        }
        
    except Exception as e:
        logger.error(f"Error computing ATS stats for team={team_abbrev}: {e}")
        return {
            "team": team_abbrev,
            "games_analyzed": 0,
            "record": "0-0-0",
            "win_pct": 0.0,
            "roi": 0.0,
            "avg_spread_diff": 0.0,
            "error": str(e)
        }


async def get_team_ou_stats(team_abbrev: str, window: int = 20) -> Dict[str, Any]:
    """
    Get team O/U statistics over last N finished games
    
    Args:
        team_abbrev: Team abbreviation
        window: Number of recent games to analyze (default: 20)
        
    Returns:
        Dict with O/U statistics including over_pct, games_analyzed, avg_total_diff
    """
    try:
        # Query last N finished games with results and closing totals
        query = """
            SELECT 
                tgr.game_id,
                tgr.points_for,
                cl.point as total_line,
                g.commence_time
            FROM team_game_results tgr
            JOIN games g ON tgr.game_id = g.id
            JOIN closing_lines cl ON tgr.game_id = cl.game_id 
                AND cl.market_type = 'totals'
            WHERE tgr.team_abbrev = $1
                AND g.status = 'final'
                AND cl.point IS NOT NULL
            ORDER BY g.commence_time DESC
            LIMIT $2
        """
        
        games = await fetch_all(query, team_abbrev, window)
        
        if not games:
            return {
                "team": team_abbrev,
                "games_analyzed": 0,
                "record": "0-0-0",
                "over_pct": 0.0,
                "avg_total_diff": 0.0,
                "avg_total_points": 0.0
            }
            
        # Get total points for each game (need to sum both teams)
        overs = 0
        unders = 0
        pushes = 0
        total_diffs = []
        total_points_list = []
        
        for game in games:
            game_id = game['game_id']
            total_line = float(game['total_line'])
            
            # Get both teams' scores for this game
            scores_query = """
                SELECT points_for
                FROM team_game_results
                WHERE game_id = $1
            """
            scores = await fetch_all(scores_query, game_id)
            
            if len(scores) != 2:
                continue
                
            total_points = sum(s['points_for'] for s in scores)
            total_points_list.append(total_points)
            total_diff = total_points - total_line
            total_diffs.append(total_diff)
            
            if total_points > total_line:
                overs += 1
            elif total_points < total_line:
                unders += 1
            else:
                pushes += 1
                
        games_analyzed = len(total_diffs)
        decided_games = overs + unders
        
        # Calculate over percentage (excluding pushes)
        over_pct = (overs / decided_games) if decided_games > 0 else 0.0
        
        # Average total differential
        avg_total_diff = sum(total_diffs) / len(total_diffs) if total_diffs else 0.0
        
        # Average total points
        avg_total_points = sum(total_points_list) / len(total_points_list) if total_points_list else 0.0
        
        return {
            "team": team_abbrev,
            "games_analyzed": games_analyzed,
            "record": f"{overs}-{unders}-{pushes}",
            "over_pct": round(over_pct, 3),
            "avg_total_diff": round(avg_total_diff, 2),
            "avg_total_points": round(avg_total_points, 1)
        }
        
    except Exception as e:
        logger.error(f"Error computing O/U stats for team={team_abbrev}: {e}")
        return {
            "team": team_abbrev,
            "games_analyzed": 0,
            "record": "0-0-0",
            "over_pct": 0.0,
            "avg_total_diff": 0.0,
            "avg_total_points": 0.0,
            "error": str(e)
        }


async def compute_all_game_results() -> Dict[str, Any]:
    """
    For all finished games without ATS/O-U results, compute and store them
    
    This function finds games with status='final' that have team_game_results
    but haven't had their ATS/O-U results computed yet, then computes and 
    caches those results.
    
    Returns:
        Dict with summary of games processed and results computed
    """
    try:
        # Find finished games with results but no cached betting results
        # We'll identify games that need processing by checking if they have
        # team_game_results and closing_lines but we haven't cached ATS/O-U results
        
        query = """
            SELECT DISTINCT g.id as game_id, g.home_team, g.away_team
            FROM games g
            JOIN team_game_results tgr ON g.id = tgr.game_id
            JOIN closing_lines cl ON g.id = cl.game_id
            WHERE g.status = 'final'
            ORDER BY g.commence_time DESC
        """
        
        games = await fetch_all(query)
        
        if not games:
            return {
                "status": "success",
                "games_processed": 0,
                "message": "No finished games found to process"
            }
            
        ats_results = []
        ou_results = []
        errors = []
        
        for game in games:
            game_id = game['game_id']
            home_team = game['home_team']
            away_team = game['away_team']
            
            # Compute ATS results for both teams
            if home_team:
                home_ats = await compute_ats_result(game_id, home_team)
                if home_ats:
                    ats_results.append({
                        "game_id": game_id,
                        "team": home_team,
                        "result": home_ats
                    })
                else:
                    errors.append(f"Failed to compute ATS for {home_team} in game {game_id}")
                    
            if away_team:
                away_ats = await compute_ats_result(game_id, away_team)
                if away_ats:
                    ats_results.append({
                        "game_id": game_id,
                        "team": away_team,
                        "result": away_ats
                    })
                else:
                    errors.append(f"Failed to compute ATS for {away_team} in game {game_id}")
                    
            # Compute O/U result for the game
            ou_result = await compute_ou_result(game_id)
            if ou_result:
                ou_results.append({
                    "game_id": game_id,
                    "result": ou_result
                })
            else:
                errors.append(f"Failed to compute O/U for game {game_id}")
                
        logger.info(
            f"Computed betting results: {len(games)} games, "
            f"{len(ats_results)} ATS results, {len(ou_results)} O/U results, "
            f"{len(errors)} errors"
        )
        
        return {
            "status": "success",
            "games_processed": len(games),
            "ats_results_computed": len(ats_results),
            "ou_results_computed": len(ou_results),
            "errors": errors[:10]  # Return first 10 errors only
        }
        
    except Exception as e:
        logger.error(f"Error computing all game results: {e}")
        return {
            "status": "error",
            "error": str(e),
            "games_processed": 0
        }
