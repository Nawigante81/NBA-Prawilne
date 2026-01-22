"""
Report service for generating daily NBA betting reports.
Generates three daily reports with betting insights and quality-gated recommendations.

Usage:
    from services.report_service import get_report_service
    from datetime import date
    
    # Generate reports
    service = get_report_service()
    
    # 7:50 AM - Previous day analysis
    report_750 = await service.generate_750am_report()
    
    # 8:00 AM - Morning summary
    report_800 = await service.generate_800am_report()
    
    # 11:00 AM - Game-day scouting with betting proposals
    report_1100 = await service.generate_1100am_report()
    
    # All reports are automatically stored in the reports table
    # and returned as structured dictionaries ready for JSON serialization
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
from zoneinfo import ZoneInfo
import logging

from db import get_db
from settings import settings
from models import Report, GateFailureReason
from services.analytics_service import get_analytics_service
from services.quality_gates import QualityGateService
from services.clv_service import CLVService
from services.betting_math import expected_value, implied_probability, american_to_decimal

logger = logging.getLogger(__name__)

# Focus teams for analysis
FOCUS_TEAMS = ["BOS", "MIN", "OKC", "ORL", "CLE", "SAC", "HOU", "NYK", "CHI"]


class ReportService:
    """Service for generating daily betting reports with quality gates."""
    
    def __init__(self):
        self.db = get_db()
        self.analytics = get_analytics_service()
        self.quality_gates = QualityGateService()
        self.clv_service = CLVService()
        self.tz = ZoneInfo(settings.timezone)
    
    async def generate_750am_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """
        7:50 AM Report - Previous Day Analysis
        
        Analyzes:
        - Results vs closing line (ATS cover/non-cover, O/U)
        - Top 3 trendy teams (consistently beating/spoiling Vegas)
        - Bulls player report (PTS/REB/AST, minutes, role note, last game + last 5 form)
        - Risks/insights for next day
        
        Args:
            report_date: Date for the report (defaults to today)
        
        Returns:
            Report content dictionary
        """
        if report_date is None:
            report_date = datetime.now(self.tz).date()
        
        logger.info(f"Generating 7:50 AM report for {report_date}")
        
        previous_day = report_date - timedelta(days=1)
        
        report_content = {
            "report_type": "750am",
            "report_date": str(report_date),
            "generated_at": datetime.now(self.tz).isoformat(),
            "sections": {}
        }
        
        # Section 1: Previous day results vs closing line
        report_content["sections"]["yesterday_results"] = await self._get_yesterday_ats_ou_results(previous_day)
        
        # Section 2: Top 3 trendy teams
        report_content["sections"]["trendy_teams"] = await self._get_top_trendy_teams()
        
        # Section 3: Bulls player breakdown
        report_content["sections"]["bulls_players"] = await self._get_bulls_player_report()
        
        # Section 4: Risks and insights for next day
        report_content["sections"]["risks_insights"] = await self._get_risks_and_insights(report_date)
        
        # Store to database
        await self._store_report("750am", report_date, report_content)
        
        return report_content
    
    async def generate_800am_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """
        8:00 AM Report - Morning Summary
        
        Includes:
        - Yesterday results: one-liner per focus team (result, ATS, O/U)
        - 7-day trends (pace, OffRtg, DefRtg, 3PT%, FT%)
        - Bulls players (last 5 form, minutes, role changes)
        - Betting leans: 2-3 directional notes
        - Action required: bookmaker screenshot upload reminder
        
        Args:
            report_date: Date for the report (defaults to today)
        
        Returns:
            Report content dictionary
        """
        if report_date is None:
            report_date = datetime.now(self.tz).date()
        
        logger.info(f"Generating 8:00 AM report for {report_date}")
        
        previous_day = report_date - timedelta(days=1)
        
        report_content = {
            "report_type": "800am",
            "report_date": str(report_date),
            "generated_at": datetime.now(self.tz).isoformat(),
            "sections": {}
        }
        
        # Section 1: Yesterday one-liners for focus teams
        report_content["sections"]["yesterday_focus_teams"] = await self._get_focus_teams_summary(previous_day)
        
        # Section 2: 7-day trends for focus teams
        report_content["sections"]["seven_day_trends"] = await self._get_seven_day_trends()
        
        # Section 3: Bulls players last 5 form
        report_content["sections"]["bulls_form"] = await self._get_bulls_last_5_form()
        
        # Section 4: Betting leans
        report_content["sections"]["betting_leans"] = await self._get_betting_leans(report_date)
        
        # Section 5: Action required
        report_content["sections"]["action_required"] = {
            "reminder": "Upload bookmaker screenshots for today's closing lines",
            "priority": "high",
            "deadline": f"{report_date} 11:00 PM CT"
        }
        
        # Store to database
        await self._store_report("800am", report_date, report_content)
        
        return report_content
    
    async def generate_1100am_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """
        11:00 AM Report - Game-Day Scouting
        
        Includes:
        - Today slate (game times, injury status/UNKNOWN if unavailable)
        - Matchup notes (pace, inside/outside, rebounding, foul rate, 3PA rate)
        - Bulls sheet (last game recap, last 5 form, positional matchups, initial lean)
        - Betting proposals WITH QUALITY GATES:
          - general parlay (3-5 legs low risk)
          - Bulls parlay (2-5 legs)
          - conservative alternatives
        - Risks (late scratches, minute restrictions, B2B, travel, line movement)
        
        Args:
            report_date: Date for the report (defaults to today)
        
        Returns:
            Report content dictionary
        """
        if report_date is None:
            report_date = datetime.now(self.tz).date()
        
        logger.info(f"Generating 11:00 AM report for {report_date}")
        
        report_content = {
            "report_type": "1100am",
            "report_date": str(report_date),
            "generated_at": datetime.now(self.tz).isoformat(),
            "sections": {}
        }
        
        # Section 1: Today's game slate
        report_content["sections"]["todays_slate"] = await self._get_todays_slate(report_date)
        
        # Section 2: Matchup notes for today's games
        report_content["sections"]["matchup_notes"] = await self._get_matchup_notes(report_date)
        
        # Section 3: Bulls game sheet (if playing today)
        report_content["sections"]["bulls_sheet"] = await self._get_bulls_game_sheet(report_date)
        
        # Section 4: Betting proposals with quality gates
        report_content["sections"]["betting_proposals"] = await self._get_betting_proposals(report_date)
        
        # Section 5: Risks
        report_content["sections"]["risks"] = await self._get_game_day_risks(report_date)
        
        # Store to database
        await self._store_report("1100am", report_date, report_content)
        
        return report_content
    
    # Private helper methods for 7:50 AM report
    
    async def _get_yesterday_ats_ou_results(self, previous_day: date) -> Dict[str, Any]:
        """Get yesterday's game results with ATS and O/U outcomes."""
        try:
            result = self.db.table("game_results").select("*").eq(
                "game_date", str(previous_day)
            ).execute()
            
            if not result.data:
                return {
                    "message": f"No games on {previous_day}",
                    "games": []
                }
            
            games = []
            for game in result.data:
                home_team = game.get("home_team")
                away_team = game.get("away_team")
                home_score = game.get("home_score")
                away_score = game.get("away_score")
                home_spread = game.get("home_spread_closing")
                total_closing = game.get("total_closing")
                
                game_summary = {
                    "matchup": f"{away_team} @ {home_team}",
                    "score": f"{away_score}-{home_score}",
                    "winner": home_team if home_score > away_score else away_team
                }
                
                # Calculate ATS
                if home_spread is not None and home_score is not None and away_score is not None:
                    home_ats_margin = home_score + home_spread - away_score
                    if abs(home_ats_margin) < 0.5:
                        ats_result = "PUSH"
                        ats_winner = "N/A"
                    elif home_ats_margin > 0:
                        ats_result = "COVER"
                        ats_winner = home_team
                    else:
                        ats_result = "NO COVER"
                        ats_winner = away_team
                    
                    game_summary["ats"] = {
                        "spread": home_spread,
                        "result": ats_result,
                        "winner": ats_winner
                    }
                
                # Calculate O/U
                if total_closing is not None and home_score is not None and away_score is not None:
                    actual_total = home_score + away_score
                    if abs(actual_total - total_closing) < 0.5:
                        ou_result = "PUSH"
                    elif actual_total > total_closing:
                        ou_result = "OVER"
                    else:
                        ou_result = "UNDER"
                    
                    game_summary["ou"] = {
                        "total": total_closing,
                        "actual": actual_total,
                        "result": ou_result
                    }
                
                games.append(game_summary)
            
            return {
                "date": str(previous_day),
                "games_count": len(games),
                "games": games
            }
        
        except Exception as e:
            logger.error(f"Error getting yesterday's results: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "games": []
            }
    
    async def _get_top_trendy_teams(self) -> Dict[str, Any]:
        """Get top 3 teams beating Vegas (hot) and top 3 missing Vegas (cold)."""
        try:
            trends = await self.analytics.get_trendy_teams(days=14)
            
            return {
                "analysis_period": "14 days",
                "hot_teams": trends.get("hot_teams", [])[:3],
                "cold_teams": trends.get("cold_teams", [])[:3],
                "note": "Hot teams consistently beat spreads; cold teams consistently miss"
            }
        
        except Exception as e:
            logger.error(f"Error getting trendy teams: {str(e)}", exc_info=True)
            return {
                "hot_teams": [],
                "cold_teams": [],
                "error": str(e)
            }
    
    async def _get_bulls_player_report(self) -> Dict[str, Any]:
        """Get comprehensive Bulls player breakdown with last game and last 5 stats."""
        try:
            breakdown = await self.analytics.get_bulls_player_breakdown()
            
            players = []
            for player_data in breakdown[:12]:  # Top 12 rotation players
                name = player_data.get("name")
                stats = player_data.get("recent_stats", {})
                
                if stats.get("games", 0) == 0:
                    continue
                
                player_info = {
                    "name": name,
                    "position": player_data.get("position", "N/A"),
                    "jersey": player_data.get("jersey_number"),
                    "last_5_avg": {
                        "points": stats.get("points_per_game"),
                        "rebounds": stats.get("rebounds_per_game"),
                        "assists": stats.get("assists_per_game"),
                        "minutes": stats.get("minutes_per_game")
                    },
                    "last_game_points": stats.get("last_3_points", [None])[0] if stats.get("last_3_points") else None,
                    "role": stats.get("role", "unknown"),
                    "games_analyzed": stats.get("games", 0)
                }
                
                players.append(player_info)
            
            return {
                "team": "Chicago Bulls",
                "players_count": len(players),
                "players": players,
                "note": "Role classifications: star (30+ min, 20+ pts), starter (25+ min, 15+ pts), rotation (20+ min)"
            }
        
        except Exception as e:
            logger.error(f"Error getting Bulls player report: {str(e)}", exc_info=True)
            return {
                "players": [],
                "error": str(e)
            }
    
    async def _get_risks_and_insights(self, report_date: date) -> Dict[str, Any]:
        """Identify risks and insights for the upcoming day."""
        risks = []
        insights = []
        
        try:
            # Check for Bulls game today
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if games_result.data:
                bulls_game = None
                for game in games_result.data:
                    if game.get("home_team") == "CHI" or game.get("away_team") == "CHI":
                        bulls_game = game
                        break
                
                if bulls_game:
                    # Check if B2B
                    yesterday = report_date - timedelta(days=1)
                    prev_result = self.db.table("game_results").select("*").eq(
                        "game_date", str(yesterday)
                    ).execute()
                    
                    if prev_result.data:
                        for prev_game in prev_result.data:
                            if prev_game.get("home_team") == "CHI" or prev_game.get("away_team") == "CHI":
                                risks.append({
                                    "type": "back_to_back",
                                    "severity": "medium",
                                    "description": "Bulls playing back-to-back games - monitor rotation and minutes"
                                })
                                break
                    
                    insights.append({
                        "type": "bulls_game",
                        "description": f"Bulls playing today: {bulls_game.get('away_team')} @ {bulls_game.get('home_team')}",
                        "action": "Review 11:00 AM report for detailed breakdown"
                    })
            
            # Generic insights
            insights.append({
                "type": "line_movement",
                "description": "Monitor line movements in the 2 hours before game time",
                "action": "Check for sharp money indicators or injury news"
            })
            
            return {
                "risks": risks,
                "insights": insights,
                "date": str(report_date)
            }
        
        except Exception as e:
            logger.error(f"Error getting risks/insights: {str(e)}", exc_info=True)
            return {
                "risks": [],
                "insights": [],
                "error": str(e)
            }
    
    # Private helper methods for 8:00 AM report
    
    async def _get_focus_teams_summary(self, previous_day: date) -> Dict[str, Any]:
        """Get one-liner summaries for focus teams from yesterday."""
        try:
            result = self.db.table("game_results").select("*").eq(
                "game_date", str(previous_day)
            ).execute()
            
            if not result.data:
                return {
                    "message": "No games yesterday",
                    "summaries": []
                }
            
            summaries = []
            for game in result.data:
                home = game.get("home_team")
                away = game.get("away_team")
                
                # Check if focus team involved
                focus_team = None
                if home in FOCUS_TEAMS:
                    focus_team = home
                    is_home = True
                elif away in FOCUS_TEAMS:
                    focus_team = away
                    is_home = False
                else:
                    continue
                
                home_score = game.get("home_score")
                away_score = game.get("away_score")
                home_spread = game.get("home_spread_closing")
                total_closing = game.get("total_closing")
                
                # Determine win/loss
                if is_home:
                    won = home_score > away_score
                    score_display = f"{home_score}-{away_score}"
                else:
                    won = away_score > home_score
                    score_display = f"{away_score}-{home_score}"
                
                # ATS
                ats_status = "N/A"
                if home_spread is not None:
                    home_ats_margin = home_score + home_spread - away_score
                    if abs(home_ats_margin) < 0.5:
                        ats_status = "PUSH"
                    elif (is_home and home_ats_margin > 0) or (not is_home and home_ats_margin < 0):
                        ats_status = "COVER"
                    else:
                        ats_status = "NO COVER"
                
                # O/U
                ou_status = "N/A"
                if total_closing is not None:
                    actual = home_score + away_score
                    if abs(actual - total_closing) < 0.5:
                        ou_status = "PUSH"
                    elif actual > total_closing:
                        ou_status = "OVER"
                    else:
                        ou_status = "UNDER"
                
                opponent = away if is_home else home
                
                summaries.append({
                    "team": focus_team,
                    "result": "W" if won else "L",
                    "score": score_display,
                    "opponent": opponent,
                    "ats": ats_status,
                    "ou": ou_status,
                    "one_liner": f"{focus_team} {'W' if won else 'L'} {score_display} vs {opponent} | ATS: {ats_status} | O/U: {ou_status}"
                })
            
            return {
                "date": str(previous_day),
                "summaries": summaries
            }
        
        except Exception as e:
            logger.error(f"Error getting focus teams summary: {str(e)}", exc_info=True)
            return {
                "summaries": [],
                "error": str(e)
            }
    
    async def _get_seven_day_trends(self) -> Dict[str, Any]:
        """Get 7-day trends for all focus teams."""
        try:
            trends = []
            
            for team in FOCUS_TEAMS:
                team_trends = await self.analytics.get_team_trends(team, days=7, min_games=3)
                
                if team_trends.get("insufficient_data"):
                    continue
                
                trends.append({
                    "team": team,
                    "games": team_trends.get("games"),
                    "pace": team_trends.get("pace"),
                    "offensive_rating": team_trends.get("offensive_rating"),
                    "defensive_rating": team_trends.get("defensive_rating"),
                    "three_point_pct": team_trends.get("three_point_pct"),
                    "free_throw_pct": team_trends.get("free_throw_pct"),
                    "points_per_game": team_trends.get("points_per_game")
                })
            
            return {
                "period": "7 days",
                "teams_count": len(trends),
                "trends": trends
            }
        
        except Exception as e:
            logger.error(f"Error getting 7-day trends: {str(e)}", exc_info=True)
            return {
                "trends": [],
                "error": str(e)
            }
    
    async def _get_bulls_last_5_form(self) -> Dict[str, Any]:
        """Get Bulls players' last 5 game form with role changes."""
        try:
            breakdown = await self.analytics.get_bulls_player_breakdown()
            
            form_data = []
            for player_data in breakdown[:10]:  # Top 10 players
                stats = player_data.get("recent_stats", {})
                
                if stats.get("games", 0) < 3:
                    continue
                
                form_data.append({
                    "name": player_data.get("name"),
                    "position": player_data.get("position"),
                    "last_5": {
                        "ppg": stats.get("points_per_game"),
                        "rpg": stats.get("rebounds_per_game"),
                        "apg": stats.get("assists_per_game"),
                        "mpg": stats.get("minutes_per_game")
                    },
                    "role": stats.get("role"),
                    "consistency": self._calculate_consistency(stats.get("last_3_points", [])),
                    "games": stats.get("games")
                })
            
            return {
                "team": "Chicago Bulls",
                "players": form_data,
                "note": "Consistency = low variance in scoring over last 3 games"
            }
        
        except Exception as e:
            logger.error(f"Error getting Bulls form: {str(e)}", exc_info=True)
            return {
                "players": [],
                "error": str(e)
            }
    
    async def _get_betting_leans(self, report_date: date) -> Dict[str, Any]:
        """Generate 2-3 directional betting notes for today."""
        leans = []
        
        try:
            # Get today's games
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if not games_result.data:
                return {
                    "leans": [],
                    "message": "No games today"
                }
            
            # Get recent ATS performance for teams playing today
            ats_performance = await self.analytics.get_ats_performance(days=14)
            
            for game in games_result.data[:5]:  # Limit to first 5 games
                home = game.get("home_team")
                away = game.get("away_team")
                
                # Find ATS records
                home_ats = next((t for t in ats_performance if t["team"] == home), None)
                away_ats = next((t for t in ats_performance if t["team"] == away), None)
                
                if home_ats and away_ats:
                    # Simple lean based on ATS performance
                    if home_ats["ats_win_pct"] > 0.60 and home_ats["games"] >= 5:
                        leans.append({
                            "game": f"{away} @ {home}",
                            "lean": f"{home} ATS",
                            "reasoning": f"{home} covering {home_ats['ats_win_pct']*100:.0f}% in last {home_ats['games']} games",
                            "confidence": "low"
                        })
                    elif away_ats["ats_win_pct"] > 0.60 and away_ats["games"] >= 5:
                        leans.append({
                            "game": f"{away} @ {home}",
                            "lean": f"{away} ATS",
                            "reasoning": f"{away} covering {away_ats['ats_win_pct']*100:.0f}% in last {away_ats['games']} games",
                            "confidence": "low"
                        })
            
            return {
                "date": str(report_date),
                "leans_count": len(leans),
                "leans": leans[:3],  # Max 3
                "disclaimer": "Leans are directional indicators only. Wait for 11:00 AM report for quality-gated picks."
            }
        
        except Exception as e:
            logger.error(f"Error getting betting leans: {str(e)}", exc_info=True)
            return {
                "leans": [],
                "error": str(e)
            }
    
    # Private helper methods for 11:00 AM report
    
    async def _get_todays_slate(self, report_date: date) -> Dict[str, Any]:
        """Get today's game slate with times and injury status."""
        try:
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).order("commence_time").execute()
            
            if not games_result.data:
                return {
                    "message": "No games scheduled today",
                    "games": []
                }
            
            slate = []
            for game in games_result.data:
                game_id = game.get("id")
                commence_time_utc = datetime.fromisoformat(game.get("commence_time").replace("Z", "+00:00"))
                commence_time_local = commence_time_utc.astimezone(self.tz)
                
                game_info = {
                    "game_id": game_id,
                    "matchup": f"{game.get('away_team')} @ {game.get('home_team')}",
                    "time_ct": commence_time_local.strftime("%I:%M %p"),
                    "home_team": game.get("home_team"),
                    "away_team": game.get("away_team"),
                    "injury_status": "UNKNOWN"  # Default - would integrate with injury API
                }
                
                slate.append(game_info)
            
            return {
                "date": str(report_date),
                "games_count": len(slate),
                "games": slate,
                "note": "Injury status requires external API integration"
            }
        
        except Exception as e:
            logger.error(f"Error getting today's slate: {str(e)}", exc_info=True)
            return {
                "games": [],
                "error": str(e)
            }
    
    async def _get_matchup_notes(self, report_date: date) -> Dict[str, Any]:
        """Get matchup analysis for today's games."""
        try:
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if not games_result.data:
                return {
                    "matchups": []
                }
            
            matchups = []
            for game in games_result.data:
                home = game.get("home_team")
                away = game.get("away_team")
                
                # Get recent trends for both teams
                home_trends = await self.analytics.get_team_trends(home, days=7, min_games=3)
                away_trends = await self.analytics.get_team_trends(away, days=7, min_games=3)
                
                matchup = {
                    "matchup": f"{away} @ {home}",
                    "pace_matchup": self._compare_metric(away_trends.get("pace"), home_trends.get("pace"), "pace"),
                    "offensive_matchup": f"{away} OffRtg: {away_trends.get('offensive_rating')} vs {home} DefRtg: {home_trends.get('defensive_rating')}",
                    "three_point_rates": {
                        "away": away_trends.get("three_point_pct"),
                        "home": home_trends.get("three_point_pct")
                    },
                    "data_quality": "sufficient" if not (home_trends.get("insufficient_data") or away_trends.get("insufficient_data")) else "limited"
                }
                
                matchups.append(matchup)
            
            return {
                "date": str(report_date),
                "matchups": matchups
            }
        
        except Exception as e:
            logger.error(f"Error getting matchup notes: {str(e)}", exc_info=True)
            return {
                "matchups": [],
                "error": str(e)
            }
    
    async def _get_bulls_game_sheet(self, report_date: date) -> Dict[str, Any]:
        """Get Bulls game sheet if playing today."""
        try:
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if not games_result.data:
                return {
                    "playing_today": False,
                    "message": "Bulls not playing today"
                }
            
            bulls_game = None
            for game in games_result.data:
                if game.get("home_team") == "CHI" or game.get("away_team") == "CHI":
                    bulls_game = game
                    break
            
            if not bulls_game:
                return {
                    "playing_today": False,
                    "message": "Bulls not playing today"
                }
            
            is_home = bulls_game.get("home_team") == "CHI"
            opponent = bulls_game.get("away_team") if is_home else bulls_game.get("home_team")
            
            # Get last game recap
            yesterday = report_date - timedelta(days=1)
            last_game_result = self.db.table("game_results").select("*").eq(
                "game_date", str(yesterday)
            ).execute()
            
            last_game_recap = "No recent game"
            if last_game_result.data:
                for lg in last_game_result.data:
                    if lg.get("home_team") == "CHI" or lg.get("away_team") == "CHI":
                        last_game_recap = f"Last game: {lg.get('away_team')} {lg.get('away_score')} @ {lg.get('home_team')} {lg.get('home_score')}"
                        break
            
            # Get Bulls and opponent trends
            bulls_trends = await self.analytics.get_team_trends("CHI", days=7, min_games=3)
            opp_trends = await self.analytics.get_team_trends(opponent, days=7, min_games=3)
            
            # Get Bulls player form
            bulls_players = await self.analytics.get_bulls_player_breakdown()
            
            return {
                "playing_today": True,
                "matchup": f"{'CHI' if not is_home else opponent} @ {'CHI' if is_home else opponent}",
                "location": "home" if is_home else "away",
                "opponent": opponent,
                "last_game": last_game_recap,
                "bulls_trends_l7": bulls_trends,
                "opponent_trends_l7": opp_trends,
                "key_players": [
                    {
                        "name": p.get("name"),
                        "role": p.get("recent_stats", {}).get("role"),
                        "ppg": p.get("recent_stats", {}).get("points_per_game")
                    }
                    for p in bulls_players[:5]
                ],
                "initial_lean": "Wait for odds analysis and quality gates"
            }
        
        except Exception as e:
            logger.error(f"Error getting Bulls game sheet: {str(e)}", exc_info=True)
            return {
                "playing_today": False,
                "error": str(e)
            }
    
    async def _get_betting_proposals(self, report_date: date) -> Dict[str, Any]:
        """Generate betting proposals with quality gates."""
        try:
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if not games_result.data:
                return {
                    "general_parlay": {"status": "NO_BET", "reason": "No games today"},
                    "bulls_parlay": {"status": "NO_BET", "reason": "No games today"},
                    "conservative_alternatives": []
                }
            
            # Collect potential picks with quality gates
            general_picks = []
            bulls_picks = []
            
            for game in games_result.data:
                game_id = game.get("id")
                home = game.get("home_team")
                away = game.get("away_team")
                
                # Check quality gates for this game
                spreads_gate = await self.quality_gates.check_odds_availability(game_id, "spreads")
                totals_gate = await self.quality_gates.check_odds_availability(game_id, "totals")
                
                if not spreads_gate.passed and not totals_gate.passed:
                    continue
                
                # Get recent odds (simplified - would query odds_snapshots)
                # For now, generate placeholder analysis
                
                if spreads_gate.passed:
                    # Check team sample size
                    home_sample = await self.quality_gates.check_team_sample_size(home)
                    away_sample = await self.quality_gates.check_team_sample_size(away)
                    
                    if home_sample.passed and away_sample.passed:
                        # This would be a real pick with EV calculation
                        # For now, mark as needing manual review
                        pick_data = {
                            "game": f"{away} @ {home}",
                            "market": "spread",
                            "status": "NEEDS_ODDS",
                            "gate_checks": {
                                "odds_available": spreads_gate.passed,
                                "sample_size": True
                            }
                        }
                        
                        if home == "CHI" or away == "CHI":
                            bulls_picks.append(pick_data)
                        else:
                            general_picks.append(pick_data)
            
            # Build parlays if we have enough quality picks
            general_parlay = self._build_parlay(general_picks, "general", min_legs=3, max_legs=5)
            bulls_parlay = self._build_parlay(bulls_picks, "bulls", min_legs=2, max_legs=5)
            
            # Conservative alternatives (singles)
            conservative = [
                {
                    "type": "single",
                    "pick": pick,
                    "reason": "Lower risk than parlay"
                }
                for pick in (general_picks + bulls_picks)[:3]
            ]
            
            return {
                "general_parlay": general_parlay,
                "bulls_parlay": bulls_parlay,
                "conservative_alternatives": conservative,
                "disclaimer": "All picks subject to quality gates. NO_BET means criteria not met."
            }
        
        except Exception as e:
            logger.error(f"Error generating betting proposals: {str(e)}", exc_info=True)
            return {
                "general_parlay": {"status": "ERROR", "error": str(e)},
                "bulls_parlay": {"status": "ERROR", "error": str(e)},
                "conservative_alternatives": []
            }
    
    async def _get_game_day_risks(self, report_date: date) -> Dict[str, Any]:
        """Identify game day risks."""
        risks = []
        
        try:
            # Late scratch risk
            risks.append({
                "type": "late_scratches",
                "severity": "high",
                "description": "Monitor injury reports 1-2 hours before tip-off",
                "mitigation": "Check official team injury reports and beat writers on Twitter"
            })
            
            # Line movement risk
            risks.append({
                "type": "line_movement",
                "severity": "medium",
                "description": "Sharp line movement can invalidate pre-game analysis",
                "mitigation": "Set alerts for >1 point spread moves or >2 point total moves"
            })
            
            # Check for B2B situations
            games_result = self.db.table("games").select("*").gte(
                "commence_time", str(report_date)
            ).lt(
                "commence_time", str(report_date + timedelta(days=1))
            ).execute()
            
            if games_result.data:
                yesterday = report_date - timedelta(days=1)
                prev_result = self.db.table("game_results").select("*").eq(
                    "game_date", str(yesterday)
                ).execute()
                
                if prev_result.data:
                    yesterday_teams = set()
                    for game in prev_result.data:
                        yesterday_teams.add(game.get("home_team"))
                        yesterday_teams.add(game.get("away_team"))
                    
                    for game in games_result.data:
                        home = game.get("home_team")
                        away = game.get("away_team")
                        
                        if home in yesterday_teams or away in yesterday_teams:
                            b2b_team = home if home in yesterday_teams else away
                            risks.append({
                                "type": "back_to_back",
                                "severity": "medium",
                                "description": f"{b2b_team} playing back-to-back",
                                "mitigation": "Expect reduced minutes for key players, monitor starting lineups"
                            })
            
            return {
                "date": str(report_date),
                "risks_count": len(risks),
                "risks": risks
            }
        
        except Exception as e:
            logger.error(f"Error getting game day risks: {str(e)}", exc_info=True)
            return {
                "risks": [],
                "error": str(e)
            }
    
    # Helper methods
    
    async def _store_report(self, report_type: str, report_date: date, content: Dict[str, Any]) -> None:
        """Store report to database."""
        try:
            report_data = {
                "report_type": report_type,
                "report_date": str(report_date),
                "content": content,
                "generated_at": datetime.now(self.tz).isoformat()
            }
            
            # Check if report already exists for this date/type
            existing = self.db.table("reports").select("id").eq(
                "report_type", report_type
            ).eq(
                "report_date", str(report_date)
            ).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing
                self.db.table("reports").update(report_data).eq(
                    "id", existing.data[0]["id"]
                ).execute()
                logger.info(f"Updated {report_type} report for {report_date}")
            else:
                # Insert new
                self.db.table("reports").insert(report_data).execute()
                logger.info(f"Stored {report_type} report for {report_date}")
        
        except Exception as e:
            logger.error(f"Error storing report: {str(e)}", exc_info=True)
    
    def _calculate_consistency(self, scores: List[Optional[int]]) -> str:
        """Calculate scoring consistency."""
        if not scores or len(scores) < 2:
            return "unknown"
        
        valid_scores = [s for s in scores if s is not None]
        if len(valid_scores) < 2:
            return "unknown"
        
        avg = sum(valid_scores) / len(valid_scores)
        variance = sum((s - avg) ** 2 for s in valid_scores) / len(valid_scores)
        std_dev = variance ** 0.5
        
        # Coefficient of variation
        cv = std_dev / avg if avg > 0 else 0
        
        if cv < 0.2:
            return "high"
        elif cv < 0.4:
            return "medium"
        else:
            return "low"
    
    def _compare_metric(self, away_val: Optional[float], home_val: Optional[float], metric_name: str) -> str:
        """Compare a metric between two teams."""
        if away_val is None or home_val is None:
            return f"{metric_name}: insufficient data"
        
        diff = abs(away_val - home_val)
        if diff < 2:
            return f"{metric_name}: similar ({away_val:.1f} vs {home_val:.1f})"
        elif away_val > home_val:
            return f"{metric_name}: away higher ({away_val:.1f} vs {home_val:.1f})"
        else:
            return f"{metric_name}: home higher ({home_val:.1f} vs {away_val:.1f})"
    
    def _build_parlay(self, picks: List[Dict[str, Any]], parlay_type: str, min_legs: int, max_legs: int) -> Dict[str, Any]:
        """Build a parlay from picks."""
        if len(picks) < min_legs:
            return {
                "status": "NO_BET",
                "reason": f"Insufficient quality picks (need {min_legs}, have {len(picks)})",
                "reason_code": "INSUFFICIENT_QUALITY_PICKS"
            }
        
        # Take up to max_legs
        selected_picks = picks[:max_legs]
        
        return {
            "status": "READY",
            "type": parlay_type,
            "legs": selected_picks,
            "leg_count": len(selected_picks),
            "note": "All legs passed quality gates"
        }


# Global instance
_report_service: Optional[ReportService] = None


def get_report_service() -> ReportService:
    """Get or create report service singleton."""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service
