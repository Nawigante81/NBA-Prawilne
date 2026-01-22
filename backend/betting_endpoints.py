"""
Backend API endpoints for betting decision support
This module adds new endpoints for:
- Team betting stats with ATS/O-U calculations
- Next game information
- Value betting metrics
- Line movement tracking
- Key players with status and minutes trends
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import statistics


async def _compute_ats_ou_stats(
    supabase,
    team_abbrev: str,
    window: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute ATS and O/U stats for a team.
    
    Args:
        supabase: Supabase client
        team_abbrev: Team abbreviation (e.g., 'CHI')
        window: Number of recent games to analyze (None = all season)
    
    Returns:
        Dictionary with ATS and O/U statistics
    """
    try:
        # Fetch game results for the team
        query = supabase.table("game_results").select("*").or_(
            f"home_team.eq.{team_abbrev},away_team.eq.{team_abbrev}"
        ).order("game_date", desc=True)
        
        if window:
            query = query.limit(window)
        
        response = await anyio.to_thread.run_sync(lambda: query.execute())
        games = response.data or []
        
        if not games:
            return None
        
        # Calculate ATS stats
        ats_wins = 0
        ats_losses = 0
        ats_pushes = 0
        ats_margins = []
        
        # Calculate O/U stats
        ou_overs = 0
        ou_unders = 0
        ou_pushes = 0
        ou_margins = []
        total_points = []
        
        for game in games:
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            home_score = game.get("home_score")
            away_score = game.get("away_score")
            
            if home_score is None or away_score is None:
                continue
            
            is_home = home_team == team_abbrev
            
            # ATS calculation
            if is_home:
                closing_spread = game.get("closing_spread_home")
                ats_result = game.get("ats_result_home")
                score_margin = home_score - away_score
            else:
                closing_spread = game.get("closing_spread_away")
                ats_result = game.get("ats_result_away")
                score_margin = away_score - home_score
            
            if closing_spread is not None:
                ats_margin = score_margin - closing_spread
                ats_margins.append(ats_margin)
                
                if ats_result == 'W':
                    ats_wins += 1
                elif ats_result == 'L':
                    ats_losses += 1
                elif ats_result == 'P':
                    ats_pushes += 1
            
            # O/U calculation
            closing_total = game.get("closing_total")
            ou_result = game.get("ou_result")
            actual_total = home_score + away_score
            total_points.append(actual_total)
            
            if closing_total is not None:
                ou_margin = actual_total - closing_total
                ou_margins.append(ou_margin)
                
                if ou_result == 'O':
                    ou_overs += 1
                elif ou_result == 'U':
                    ou_unders += 1
                elif ou_result == 'P':
                    ou_pushes += 1
        
        # Calculate averages and percentages
        ats_total = ats_wins + ats_losses
        ats_pct = ats_wins / ats_total if ats_total > 0 else 0
        avg_ats_margin = statistics.mean(ats_margins) if ats_margins else 0
        
        ou_total = ou_overs + ou_unders
        ou_pct = ou_overs / ou_total if ou_total > 0 else 0
        avg_ou_margin = statistics.mean(ou_margins) if ou_margins else 0
        avg_total = statistics.mean(total_points) if total_points else 0
        
        return {
            "ats": {
                "wins": ats_wins,
                "losses": ats_losses,
                "pushes": ats_pushes,
                "percentage": ats_pct,
                "avg_margin": avg_ats_margin,
            },
            "ou": {
                "overs": ou_overs,
                "unders": ou_unders,
                "pushes": ou_pushes,
                "percentage": ou_pct,
                "avg_margin": avg_ou_margin,
            },
            "avg_total_points": avg_total,
            "games_analyzed": len(games),
        }
    except Exception as e:
        logger.error(f"Error computing ATS/OU stats: {e}")
        return None


async def _get_next_game_info(supabase, team_abbrev: str) -> Optional[Dict[str, Any]]:
    """
    Get information about team's next scheduled game.
    
    Args:
        supabase: Supabase client
        team_abbrev: Team abbreviation
    
    Returns:
        Dictionary with next game information or None
    """
    try:
        now = datetime.now()
        
        # Query for upcoming games
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("games")
            .select("*")
            .or_(f"home_team.eq.{team_abbrev},away_team.eq.{team_abbrev}")
            .gte("commence_time", now.isoformat())
            .order("commence_time", desc=False)
            .limit(1)
            .execute()
        )
        
        games = response.data or []
        if not games:
            return None
        
        game = games[0]
        home_team = game.get("home_team")
        away_team = game.get("away_team")
        is_home = home_team == team_abbrev
        
        return {
            "game_id": game.get("id"),
            "opponent": away_team if is_home else home_team,
            "opponent_abbrev": away_team if is_home else home_team,
            "commence_time": game.get("commence_time"),
            "is_home": is_home,
            "venue": game.get("venue"),
            "status": game.get("status"),
        }
    except Exception as e:
        logger.error(f"Error getting next game: {e}")
        return None


async def _get_current_odds(supabase, game_id: str) -> Dict[str, Any]:
    """
    Get current odds for a game across different markets.
    
    Args:
        supabase: Supabase client
        game_id: Game ID
    
    Returns:
        Dictionary with current odds by market type
    """
    try:
        # Get latest odds for the game
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("odds")
            .select("*")
            .eq("game_id", game_id)
            .order("last_update", desc=True)
            .execute()
        )
        
        odds_rows = response.data or []
        
        # Group by market type and bookmaker, keep most recent
        by_market = {}
        for row in odds_rows:
            market_type = row.get("market_type")
            if market_type not in by_market:
                by_market[market_type] = []
            by_market[market_type].append(row)
        
        return by_market
    except Exception as e:
        logger.error(f"Error getting current odds: {e}")
        return {}


async def _get_odds_movement(
    supabase, 
    game_id: str, 
    market_type: str
) -> Optional[Dict[str, Any]]:
    """
    Get odds movement history for a specific market.
    
    Args:
        supabase: Supabase client
        game_id: Game ID
        market_type: Market type ('spread', 'totals', 'h2h')
    
    Returns:
        Dictionary with opening, current, and historical snapshots
    """
    try:
        # Get snapshots from odds_snapshots table
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("odds_snapshots")
            .select("*")
            .eq("game_id", game_id)
            .eq("market_type", market_type)
            .order("ts", desc=False)
            .execute()
        )
        
        snapshots = response.data or []
        if not snapshots:
            return None
        
        opening = snapshots[0]
        current = snapshots[-1]
        
        # Calculate movement
        opening_value = opening.get("point") or opening.get("price")
        current_value = current.get("point") or current.get("price")
        
        if opening_value is not None and current_value is not None:
            value_change = current_value - opening_value
            direction = 'UP' if value_change > 0.5 else ('DOWN' if value_change < -0.5 else 'STABLE')
        else:
            value_change = 0
            direction = 'STABLE'
        
        return {
            "market_type": market_type,
            "opening": {
                "timestamp": opening.get("ts"),
                "value": opening_value,
                "bookmaker": opening.get("bookmaker_title", opening.get("bookmaker_key")),
            },
            "current": {
                "timestamp": current.get("ts"),
                "value": current_value,
                "bookmaker": current.get("bookmaker_title", current.get("bookmaker_key")),
            },
            "movement": {
                "value_change": value_change,
                "direction": direction,
            },
            "history": [
                {
                    "timestamp": s.get("ts"),
                    "value": s.get("point") or s.get("price"),
                    "bookmaker": s.get("bookmaker_title", s.get("bookmaker_key")),
                }
                for s in snapshots
            ],
        }
    except Exception as e:
        logger.error(f"Error getting odds movement: {e}")
        return None


async def _get_key_players_with_status(
    supabase, 
    team_abbrev: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get key players for a team with injury status and minutes trends.
    
    Args:
        supabase: Supabase client
        team_abbrev: Team abbreviation
        limit: Number of players to return
    
    Returns:
        List of player dictionaries with status and trends
    """
    try:
        # Get top players by average minutes from recent games
        response = await anyio.to_thread.run_sync(
            lambda: supabase.table("player_game_stats")
            .select("player_name, minutes")
            .eq("team_tricode", team_abbrev)
            .order("game_date", desc=True)
            .limit(100)
            .execute()
        )
        
        stats_rows = response.data or []
        
        # Group by player and calculate averages
        by_player = {}
        for row in stats_rows:
            player_name = row.get("player_name")
            minutes_str = row.get("minutes")
            
            if not player_name or not minutes_str:
                continue
            
            # Parse minutes (format: "MM:SS")
            try:
                if ":" in minutes_str:
                    mm, ss = minutes_str.split(":")
                    minutes = float(mm) + float(ss) / 60.0
                else:
                    minutes = float(minutes_str)
            except:
                continue
            
            if player_name not in by_player:
                by_player[player_name] = []
            by_player[player_name].append(minutes)
        
        # Calculate stats for each player
        players = []
        for player_name, minutes_list in by_player.items():
            if len(minutes_list) < 2:
                continue
            
            last_5 = minutes_list[:5]
            prev_5 = minutes_list[5:10] if len(minutes_list) >= 10 else minutes_list[:5]
            
            avg_last_5 = statistics.mean(last_5)
            avg_prev = statistics.mean(prev_5)
            
            change = avg_last_5 - avg_prev
            direction = 'UP' if change > 2 else ('DOWN' if change < -2 else 'STABLE')
            
            players.append({
                "player_name": player_name,
                "team": team_abbrev,
                "status": "ACTIVE",  # Default, would need injury data integration
                "minutes_last_5_avg": avg_last_5,
                "minutes_trend": {
                    "change": change,
                    "direction": direction,
                },
            })
        
        # Sort by average minutes and return top N
        players.sort(key=lambda p: p["minutes_last_5_avg"], reverse=True)
        return players[:limit]
        
    except Exception as e:
        logger.error(f"Error getting key players: {e}")
        return []


def _calculate_ev_and_kelly(
    odds: float,
    model_prob: float,
    bankroll: float = 1000
) -> Dict[str, Any]:
    """
    Calculate Expected Value and Kelly Criterion stake recommendations.
    
    Args:
        odds: Decimal odds
        model_prob: Model's win probability (0-1)
        bankroll: Total bankroll amount
    
    Returns:
        Dictionary with EV, stake recommendations, and risk level
    """
    # Implied probability from odds
    implied_prob = 1.0 / odds
    
    # Edge
    edge = model_prob - implied_prob
    
    # Expected Value (per $1 stake)
    ev = (model_prob * (odds - 1)) - (1 - model_prob)
    ev_percentage = ev * 100
    
    # Kelly Criterion
    # f = (bp - q) / b
    # where b = odds - 1, p = win prob, q = lose prob
    b = odds - 1
    q = 1 - model_prob
    
    kelly_full = (b * model_prob - q) / b if b > 0 else 0
    kelly_full = max(0, min(kelly_full, 0.25))  # Clamp to 0-25%
    
    kelly_half = kelly_full * 0.5
    recommended = min(kelly_half * bankroll, bankroll * 0.03)  # Max 3% of bankroll
    
    # Risk level based on edge and stake size
    if edge < 0.02:
        risk_level = 'HIGH'
    elif recommended / bankroll > 0.02:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return {
        "implied_prob": implied_prob,
        "model_prob": model_prob,
        "edge": edge * 100,  # as percentage points
        "ev": ev,
        "ev_percentage": ev_percentage,
        "recommendation": 'VALUE' if ev_percentage >= 2.0 else 'PASS',
        "stake_recommendations": {
            "kelly_full": kelly_full * bankroll,
            "kelly_half": kelly_half * bankroll,
            "recommended": recommended,
            "risk_level": risk_level,
        },
    }
