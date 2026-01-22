"""
Analytics service for computing team and player performance metrics.
Provides trend analysis, role detection, and betting performance tracking.
"""
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional
from db import get_db
from settings import settings
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for team and player analytics with betting insights."""
    
    def __init__(self):
        self.db = get_db()
    
    async def get_team_trends(
        self, 
        team_abbr: str, 
        days: int = 7,
        min_games: int = 3
    ) -> Dict[str, Any]:
        """
        Get team performance trends over last N days.
        
        Args:
            team_abbr: Team abbreviation (e.g., "CHI")
            days: Number of days to analyze (default: 7)
            min_games: Minimum games required (default: 3)
        
        Returns:
            Dictionary with team metrics: pace, OffRtg, DefRtg, 3PT%, FT%, points, assists
        """
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            # Query team_game_stats for recent games
            result = self.db.table("team_game_stats").select("*").eq(
                "team_abbreviation", team_abbr
            ).gte(
                "game_date", str(cutoff_date)
            ).order(
                "game_date", desc=True
            ).execute()
            
            if not result.data or len(result.data) < min_games:
                return {
                    "team": team_abbr,
                    "games": 0,
                    "insufficient_data": True,
                    "message": f"Only {len(result.data) if result.data else 0} games in last {days} days"
                }
            
            games = result.data
            
            # Calculate averages
            pace_avg = self._safe_avg([g.get("pace") for g in games])
            off_rtg_avg = self._safe_avg([g.get("offensive_rating") for g in games])
            def_rtg_avg = self._safe_avg([g.get("defensive_rating") for g in games])
            
            # Calculate shooting percentages
            three_pt_pct = self._calculate_shooting_pct(
                [g.get("three_point_made") for g in games],
                [g.get("three_point_attempted") for g in games]
            )
            ft_pct = self._calculate_shooting_pct(
                [g.get("free_throws_made") for g in games],
                [g.get("free_throws_attempted") for g in games]
            )
            
            points_avg = self._safe_avg([g.get("points") for g in games])
            assists_avg = self._safe_avg([g.get("assists") for g in games])
            
            return {
                "team": team_abbr,
                "games": len(games),
                "days": days,
                "pace": round(pace_avg, 2) if pace_avg else None,
                "offensive_rating": round(off_rtg_avg, 2) if off_rtg_avg else None,
                "defensive_rating": round(def_rtg_avg, 2) if def_rtg_avg else None,
                "three_point_pct": round(three_pt_pct, 3) if three_pt_pct else None,
                "free_throw_pct": round(ft_pct, 3) if ft_pct else None,
                "points_per_game": round(points_avg, 1) if points_avg else None,
                "assists_per_game": round(assists_avg, 1) if assists_avg else None,
                "game_dates": [g.get("game_date") for g in games]
            }
        
        except Exception as e:
            logger.error(f"Error getting team trends for {team_abbr}: {str(e)}", exc_info=True)
            return {
                "team": team_abbr,
                "error": str(e)
            }
    
    async def get_player_last_n_games(
        self, 
        player_id: str, 
        n_games: int = 5
    ) -> Dict[str, Any]:
        """
        Get player performance over last N games.
        
        Args:
            player_id: Player ID (UUID)
            n_games: Number of recent games (default: 5)
        
        Returns:
            Dictionary with player stats and role analysis
        """
        try:
            # Query player_game_stats
            result = self.db.table("player_game_stats").select("*").eq(
                "player_id", player_id
            ).order(
                "game_date", desc=True
            ).limit(n_games).execute()
            
            if not result.data or len(result.data) == 0:
                return {
                    "player_id": player_id,
                    "games": 0,
                    "insufficient_data": True
                }
            
            games = result.data
            
            # Calculate averages
            pts_avg = self._safe_avg([g.get("points") for g in games])
            reb_avg = self._safe_avg([g.get("rebounds") for g in games])
            ast_avg = self._safe_avg([g.get("assists") for g in games])
            min_avg = self._safe_avg([g.get("minutes") for g in games])
            
            # Role analysis
            role = self._determine_player_role(pts_avg, min_avg)
            
            return {
                "player_id": player_id,
                "games": len(games),
                "points_per_game": round(pts_avg, 1) if pts_avg else None,
                "rebounds_per_game": round(reb_avg, 1) if reb_avg else None,
                "assists_per_game": round(ast_avg, 1) if ast_avg else None,
                "minutes_per_game": round(min_avg, 1) if min_avg else None,
                "role": role,
                "game_dates": [g.get("game_date") for g in games],
                "last_3_points": [g.get("points") for g in games[:3]]
            }
        
        except Exception as e:
            logger.error(f"Error getting player stats for {player_id}: {str(e)}", exc_info=True)
            return {
                "player_id": player_id,
                "error": str(e)
            }
    
    async def get_bulls_player_breakdown(self) -> List[Dict[str, Any]]:
        """
        Get detailed breakdown of all Bulls players with recent performance.
        
        Returns:
            List of player dictionaries with stats and analysis
        """
        try:
            # Get all active Bulls players
            players_result = self.db.table("players").select("*").eq(
                "team_abbreviation", "CHI"
            ).eq(
                "is_active", True
            ).execute()
            
            if not players_result.data:
                return []
            
            breakdown = []
            for player in players_result.data:
                player_id = player.get("id")
                
                # Get recent stats
                stats = await self.get_player_last_n_games(player_id, n_games=5)
                
                breakdown.append({
                    "name": player.get("name"),
                    "player_id": player_id,
                    "position": player.get("position"),
                    "jersey_number": player.get("jersey_number"),
                    "recent_stats": stats
                })
            
            # Sort by minutes per game (most important players first)
            breakdown.sort(
                key=lambda x: x["recent_stats"].get("minutes_per_game", 0) or 0, 
                reverse=True
            )
            
            return breakdown
        
        except Exception as e:
            logger.error(f"Error getting Bulls breakdown: {str(e)}", exc_info=True)
            return []
    
    async def get_ats_performance(
        self, 
        team_abbr: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get ATS (Against The Spread) performance vs closing lines.
        
        Args:
            team_abbr: Optional team filter
            days: Days to analyze (default: 30)
        
        Returns:
            List of teams with ATS records
        """
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            # Query game_results table
            query = self.db.table("game_results").select("*").gte(
                "game_date", str(cutoff_date)
            )
            
            if team_abbr:
                query = query.or_(f"home_team.eq.{team_abbr},away_team.eq.{team_abbr}")
            
            result = query.execute()
            
            if not result.data:
                return []
            
            # Aggregate ATS records by team
            team_records = {}
            
            for game in result.data:
                home = game.get("home_team")
                away = game.get("away_team")
                home_score = game.get("home_score")
                away_score = game.get("away_score")
                home_spread = game.get("home_spread_closing")
                
                if home_score is None or away_score is None or home_spread is None:
                    continue
                
                # Calculate ATS result
                home_cover = (home_score + home_spread) > away_score
                away_cover = not home_cover
                
                # Update home team record
                if home not in team_records:
                    team_records[home] = {"wins": 0, "losses": 0, "pushes": 0}
                
                if abs((home_score + home_spread) - away_score) < 0.5:
                    team_records[home]["pushes"] += 1
                elif home_cover:
                    team_records[home]["wins"] += 1
                else:
                    team_records[home]["losses"] += 1
                
                # Update away team record
                if away not in team_records:
                    team_records[away] = {"wins": 0, "losses": 0, "pushes": 0}
                
                if abs((home_score + home_spread) - away_score) < 0.5:
                    team_records[away]["pushes"] += 1
                elif away_cover:
                    team_records[away]["wins"] += 1
                else:
                    team_records[away]["losses"] += 1
            
            # Format results
            results = []
            for team, record in team_records.items():
                total = record["wins"] + record["losses"]
                win_pct = record["wins"] / total if total > 0 else 0
                
                results.append({
                    "team": team,
                    "ats_wins": record["wins"],
                    "ats_losses": record["losses"],
                    "ats_pushes": record["pushes"],
                    "ats_win_pct": round(win_pct, 3),
                    "games": total
                })
            
            # Sort by win percentage
            results.sort(key=lambda x: x["ats_win_pct"], reverse=True)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting ATS performance: {str(e)}", exc_info=True)
            return []
    
    async def get_over_under_performance(
        self, 
        team_abbr: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get Over/Under performance vs closing totals.
        
        Args:
            team_abbr: Optional team filter
            days: Days to analyze (default: 30)
        
        Returns:
            List of teams with O/U records
        """
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            query = self.db.table("game_results").select("*").gte(
                "game_date", str(cutoff_date)
            )
            
            if team_abbr:
                query = query.or_(f"home_team.eq.{team_abbr},away_team.eq.{team_abbr}")
            
            result = query.execute()
            
            if not result.data:
                return []
            
            # Aggregate O/U records
            team_records = {}
            
            for game in result.data:
                home = game.get("home_team")
                away = game.get("away_team")
                home_score = game.get("home_score")
                away_score = game.get("away_score")
                total_closing = game.get("total_closing")
                
                if home_score is None or away_score is None or total_closing is None:
                    continue
                
                actual_total = home_score + away_score
                went_over = actual_total > total_closing
                
                # Update both teams
                for team in [home, away]:
                    if team not in team_records:
                        team_records[team] = {"overs": 0, "unders": 0, "pushes": 0}
                    
                    if abs(actual_total - total_closing) < 0.5:
                        team_records[team]["pushes"] += 1
                    elif went_over:
                        team_records[team]["overs"] += 1
                    else:
                        team_records[team]["unders"] += 1
            
            # Format results
            results = []
            for team, record in team_records.items():
                total = record["overs"] + record["unders"]
                over_pct = record["overs"] / total if total > 0 else 0
                
                results.append({
                    "team": team,
                    "overs": record["overs"],
                    "unders": record["unders"],
                    "pushes": record["pushes"],
                    "over_pct": round(over_pct, 3),
                    "games": total
                })
            
            # Sort by over percentage
            results.sort(key=lambda x: x["over_pct"], reverse=True)
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting O/U performance: {str(e)}", exc_info=True)
            return []
    
    async def get_trendy_teams(self, days: int = 14) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get teams that are beating or missing Vegas expectations.
        
        Args:
            days: Days to analyze (default: 14)
        
        Returns:
            Dictionary with "hot" and "cold" teams
        """
        try:
            # Get ATS and O/U performance
            ats_perf = await self.get_ats_performance(days=days)
            ou_perf = await self.get_over_under_performance(days=days)
            
            # Combine metrics
            team_trends = {}
            
            for record in ats_perf:
                team = record["team"]
                team_trends[team] = {
                    "team": team,
                    "ats_win_pct": record["ats_win_pct"],
                    "ats_record": f"{record['ats_wins']}-{record['ats_losses']}",
                    "games": record["games"]
                }
            
            for record in ou_perf:
                team = record["team"]
                if team in team_trends:
                    team_trends[team]["over_pct"] = record["over_pct"]
                    team_trends[team]["ou_record"] = f"{record['overs']}-{record['unders']}"
            
            # Calculate "trend score" (simple: ATS win % is main factor)
            teams_list = list(team_trends.values())
            teams_list.sort(key=lambda x: x.get("ats_win_pct", 0), reverse=True)
            
            # Top 5 hot teams (beating expectations)
            hot_teams = [t for t in teams_list if t.get("games", 0) >= 5][:5]
            
            # Top 5 cold teams (missing expectations)
            cold_teams = [t for t in teams_list if t.get("games", 0) >= 5][-5:]
            cold_teams.reverse()
            
            return {
                "days": days,
                "hot_teams": hot_teams,
                "cold_teams": cold_teams
            }
        
        except Exception as e:
            logger.error(f"Error getting trendy teams: {str(e)}", exc_info=True)
            return {
                "hot_teams": [],
                "cold_teams": []
            }
    
    # Helper methods
    
    def _safe_avg(self, values: List[Optional[float]]) -> Optional[float]:
        """Calculate average, ignoring None values."""
        valid = [v for v in values if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)
    
    def _calculate_shooting_pct(
        self, 
        made: List[Optional[int]], 
        attempted: List[Optional[int]]
    ) -> Optional[float]:
        """Calculate shooting percentage from lists of made/attempted."""
        total_made = sum(m for m in made if m is not None)
        total_attempted = sum(a for a in attempted if a is not None)
        
        if total_attempted == 0:
            return None
        
        return total_made / total_attempted
    
    def _determine_player_role(
        self, 
        points_per_game: Optional[float], 
        minutes_per_game: Optional[float]
    ) -> str:
        """Determine player role based on usage."""
        if points_per_game is None or minutes_per_game is None:
            return "unknown"
        
        if minutes_per_game >= 30 and points_per_game >= 20:
            return "star"
        elif minutes_per_game >= 25 and points_per_game >= 15:
            return "starter"
        elif minutes_per_game >= 20:
            return "rotation"
        elif minutes_per_game >= 10:
            return "bench"
        else:
            return "deep_bench"


# Global instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create analytics service singleton."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
