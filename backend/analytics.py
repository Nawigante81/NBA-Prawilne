"""
Advanced NBA Analytics Module
- Prop Bet Predictions
- Matchup Analysis
- Form Tracking
- Injury Impact Analysis
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
import numpy as np
from supabase import Client


class PropBetPredictor:
    """Predicts player prop bets based on historical data"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def analyze_prop(
        self, 
        player_name: str, 
        stat_type: str,  # 'points', 'rebounds_total', 'assists'
        line: float,
        games_to_analyze: int = 20,
        opponent: Optional[str] = None
    ) -> Dict:
        """
        Analyze if a prop bet has value
        
        Returns:
        {
            'player': str,
            'stat_type': str,
            'line': float,
            'prediction': float,
            'hit_rate': float,  # % of times player went over line historically
            'value': str,  # 'OVER', 'UNDER', or 'NO VALUE'
            'confidence': float,  # 0-100
            'recent_games': List[Dict],
            'vs_opponent': Dict (if opponent provided)
        }
        """
        
        # Get recent games
        query = self.supabase.table('player_game_stats') \
            .select('*') \
            .eq('player_name', player_name) \
            .order('game_date', desc=True) \
            .limit(games_to_analyze)
        
        # Filter by opponent if provided
        if opponent:
            query = query.ilike('matchup', f'%{opponent}%')
        
        result = query.execute()
        games = result.data
        
        if not games or len(games) < 5:
            return {
                'error': 'Insufficient data',
                'games_found': len(games) if games else 0
            }
        
        # Extract stat values
        stat_values = [game.get(stat_type, 0) for game in games]
        
        # Calculate statistics
        avg = statistics.mean(stat_values)
        median = statistics.median(stat_values)
        std_dev = statistics.stdev(stat_values) if len(stat_values) > 1 else 0
        
        # Calculate hit rate (how often player goes over the line)
        over_count = sum(1 for val in stat_values if val > line)
        hit_rate = (over_count / len(stat_values)) * 100
        
        # Determine value
        value = 'NO VALUE'
        confidence = 0
        
        if hit_rate >= 65:
            value = 'OVER'
            confidence = min(hit_rate, 95)
        elif hit_rate <= 35:
            value = 'UNDER'
            confidence = min(100 - hit_rate, 95)
        
        # Calculate trend (last 5 vs previous games)
        if len(stat_values) >= 10:
            recent_5 = statistics.mean(stat_values[:5])
            previous_5 = statistics.mean(stat_values[5:10])
            trend = ((recent_5 - previous_5) / previous_5) * 100
        else:
            trend = 0
        
        # Analyze vs specific opponent if provided
        vs_opponent_data = None
        if opponent:
            vs_opponent_stats = [game.get(stat_type, 0) for game in games]
            if vs_opponent_stats:
                vs_opponent_data = {
                    'games': len(vs_opponent_stats),
                    'avg': statistics.mean(vs_opponent_stats),
                    'high': max(vs_opponent_stats),
                    'low': min(vs_opponent_stats),
                    'over_rate': (sum(1 for v in vs_opponent_stats if v > line) / len(vs_opponent_stats)) * 100
                }
        
        return {
            'player': player_name,
            'stat_type': stat_type,
            'line': line,
            'prediction': round(avg, 1),
            'median': round(median, 1),
            'std_dev': round(std_dev, 2),
            'hit_rate': round(hit_rate, 1),
            'value': value,
            'confidence': round(confidence, 1),
            'trend': round(trend, 1),
            'sample_size': len(stat_values),
            'recent_games': stat_values[:10],
            'vs_opponent': vs_opponent_data,
            'recommendation': self._generate_recommendation(value, confidence, hit_rate, avg, line)
        }
    
    def _generate_recommendation(self, value: str, confidence: float, hit_rate: float, avg: float, line: float) -> str:
        """Generate human-readable recommendation"""
        if value == 'NO VALUE':
            return f"No clear edge. Hit rate {hit_rate:.0f}% is too close to 50%."
        
        diff = abs(avg - line)
        
        if value == 'OVER':
            if confidence >= 80:
                return f"STRONG OVER. Player averages {avg:.1f} vs line {line}. Hits over {hit_rate:.0f}% of the time."
            else:
                return f"LEAN OVER. Avg {avg:.1f} vs {line}. {hit_rate:.0f}% hit rate."
        else:
            if confidence >= 80:
                return f"STRONG UNDER. Player averages {avg:.1f} vs line {line}. Goes under {100-hit_rate:.0f}% of the time."
            else:
                return f"LEAN UNDER. Avg {avg:.1f} vs {line}. {100-hit_rate:.0f}% under rate."


class MatchupAnalyzer:
    """Analyzes team and player matchups based on historical data"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def analyze_team_matchup(
        self, 
        team: str,  # e.g., 'CHI'
        opponent: str,  # e.g., 'LAL'
        seasons_back: int = 3
    ) -> Dict:
        """
        Analyze how a team performs against specific opponent
        
        Returns head-to-head stats, home/away splits, trends
        """
        
        # Get cutoff date (seasons_back years ago)
        cutoff_date = datetime.now() - timedelta(days=365 * seasons_back)
        
        # Get all games for team vs opponent
        result = self.supabase.table('player_game_stats') \
            .select('*') \
            .eq('team_tricode', team) \
            .ilike('matchup', f'%{opponent}%') \
            .gte('game_date', cutoff_date.date()) \
            .execute()
        
        games = result.data
        
        if not games:
            return {'error': 'No matchup data found'}
        
        # Group by game
        games_by_id = {}
        for stat in games:
            game_id = stat['game_id']
            if game_id not in games_by_id:
                games_by_id[game_id] = {
                    'game_id': game_id,
                    'date': stat['game_date'],
                    'matchup': stat['matchup'],
                    'is_home': '@' not in stat['matchup'],
                    'players': []
                }
            games_by_id[game_id]['players'].append(stat)
        
        # Calculate team totals per game
        game_totals = []
        for game_id, game_data in games_by_id.items():
            team_points = sum(p['points'] for p in game_data['players'])
            team_rebounds = sum(p['rebounds_total'] for p in game_data['players'])
            team_assists = sum(p['assists'] for p in game_data['players'])
            
            game_totals.append({
                'date': game_data['date'],
                'is_home': game_data['is_home'],
                'points': team_points,
                'rebounds': team_rebounds,
                'assists': team_assists
            })
        
        # Split home/away
        home_games = [g for g in game_totals if g['is_home']]
        away_games = [g for g in game_totals if not g['is_home']]
        
        # Calculate averages
        avg_points = statistics.mean([g['points'] for g in game_totals]) if game_totals else 0
        avg_rebounds = statistics.mean([g['rebounds'] for g in game_totals]) if game_totals else 0
        avg_assists = statistics.mean([g['assists'] for g in game_totals]) if game_totals else 0
        
        home_avg_points = statistics.mean([g['points'] for g in home_games]) if home_games else 0
        away_avg_points = statistics.mean([g['points'] for g in away_games]) if away_games else 0
        
        return {
            'team': team,
            'opponent': opponent,
            'total_games': len(game_totals),
            'home_games': len(home_games),
            'away_games': len(away_games),
            'averages': {
                'points': round(avg_points, 1),
                'rebounds': round(avg_rebounds, 1),
                'assists': round(avg_assists, 1)
            },
            'home_away_split': {
                'home_ppg': round(home_avg_points, 1),
                'away_ppg': round(away_avg_points, 1),
                'home_advantage': round(home_avg_points - away_avg_points, 1)
            },
            'recent_games': sorted(game_totals, key=lambda x: x['date'], reverse=True)[:5]
        }
    
    async def analyze_player_vs_opponent(
        self,
        player_name: str,
        opponent: str,
        seasons_back: int = 3
    ) -> Dict:
        """Analyze individual player performance vs specific opponent"""
        
        cutoff_date = datetime.now() - timedelta(days=365 * seasons_back)
        
        result = self.supabase.table('player_game_stats') \
            .select('*') \
            .eq('player_name', player_name) \
            .ilike('matchup', f'%{opponent}%') \
            .gte('game_date', cutoff_date.date()) \
            .order('game_date', desc=True) \
            .execute()
        
        games = result.data
        
        if not games:
            return {'error': 'No data found for this matchup'}
        
        # Calculate stats
        points = [g['points'] for g in games]
        rebounds = [g['rebounds_total'] for g in games]
        assists = [g['assists'] for g in games]
        
        return {
            'player': player_name,
            'opponent': opponent,
            'games_played': len(games),
            'averages': {
                'points': round(statistics.mean(points), 1),
                'rebounds': round(statistics.mean(rebounds), 1),
                'assists': round(statistics.mean(assists), 1)
            },
            'highs': {
                'points': max(points),
                'rebounds': max(rebounds),
                'assists': max(assists)
            },
            'recent_games': [
                {
                    'date': g['game_date'],
                    'matchup': g['matchup'],
                    'points': g['points'],
                    'rebounds': g['rebounds_total'],
                    'assists': g['assists'],
                    'minutes': g['minutes']
                }
                for g in games[:5]
            ]
        }


class FormTracker:
    """Tracks player form and trends over time"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def get_player_form(
        self,
        player_name: str,
        games: int = 15
    ) -> Dict:
        """
        Get player's recent form with rolling averages and trend analysis
        
        Returns form data suitable for charting
        """
        
        result = self.supabase.table('player_game_stats') \
            .select('*') \
            .eq('player_name', player_name) \
            .order('game_date', desc=True) \
            .limit(games) \
            .execute()
        
        game_stats = result.data
        
        if not game_stats or len(game_stats) < 3:
            return {'error': 'Insufficient data'}
        
        # Reverse to get chronological order for calculations
        game_stats.reverse()
        
        # Calculate rolling averages (5-game)
        rolling_data = []
        for i in range(len(game_stats)):
            start_idx = max(0, i - 4)
            window = game_stats[start_idx:i+1]
            
            rolling_data.append({
                'game_num': i + 1,
                'date': game_stats[i]['game_date'],
                'opponent': game_stats[i]['matchup'].split()[-1],
                'actual_points': game_stats[i]['points'],
                'actual_rebounds': game_stats[i]['rebounds_total'],
                'actual_assists': game_stats[i]['assists'],
                'rolling_avg_points': round(statistics.mean([g['points'] for g in window]), 1),
                'rolling_avg_rebounds': round(statistics.mean([g['rebounds_total'] for g in window]), 1),
                'rolling_avg_assists': round(statistics.mean([g['assists'] for g in window]), 1),
                'minutes': game_stats[i]['minutes']
            })
        
        # Calculate trend (comparing first half to second half)
        mid_point = len(game_stats) // 2
        first_half = game_stats[:mid_point]
        second_half = game_stats[mid_point:]
        
        first_half_ppg = statistics.mean([g['points'] for g in first_half])
        second_half_ppg = statistics.mean([g['points'] for g in second_half])
        trend = ((second_half_ppg - first_half_ppg) / first_half_ppg) * 100
        
        # Determine trend direction
        if trend > 10:
            trend_direction = 'IMPROVING'
        elif trend < -10:
            trend_direction = 'DECLINING'
        else:
            trend_direction = 'STABLE'
        
        return {
            'player': player_name,
            'games_analyzed': len(game_stats),
            'current_averages': {
                'points': round(statistics.mean([g['points'] for g in game_stats]), 1),
                'rebounds': round(statistics.mean([g['rebounds_total'] for g in game_stats]), 1),
                'assists': round(statistics.mean([g['assists'] for g in game_stats]), 1)
            },
            'trend': {
                'direction': trend_direction,
                'percentage': round(trend, 1),
                'description': f"Points {'up' if trend > 0 else 'down'} {abs(trend):.1f}% over last {len(game_stats)} games"
            },
            'games': rolling_data,
            'last_5_games': {
                'points': round(statistics.mean([g['points'] for g in game_stats[-5:]]), 1),
                'rebounds': round(statistics.mean([g['rebounds_total'] for g in game_stats[-5:]]), 1),
                'assists': round(statistics.mean([g['assists'] for g in game_stats[-5:]]), 1)
            }
        }


class InjuryImpactAnalyzer:
    """Analyzes impact of player absence on team performance"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    async def analyze_player_absence_impact(
        self,
        team: str,
        missing_player: str,
        seasons_back: int = 2
    ) -> Dict:
        """
        Analyze how team/players perform when a key player is out
        
        Looks for games where player has DNP or 0 minutes
        """
        
        cutoff_date = datetime.now() - timedelta(days=365 * seasons_back)
        
        # Get all team games
        all_games_result = self.supabase.table('player_game_stats') \
            .select('*') \
            .eq('team_tricode', team) \
            .gte('game_date', cutoff_date.date()) \
            .execute()
        
        all_games = all_games_result.data
        
        # Group by game_id
        games_by_id = {}
        for stat in all_games:
            game_id = stat['game_id']
            if game_id not in games_by_id:
                games_by_id[game_id] = []
            games_by_id[game_id].append(stat)
        
        # Separate games WITH and WITHOUT the player
        games_with_player = []
        games_without_player = []
        
        for game_id, players in games_by_id.items():
            player_in_game = False
            player_played = False
            
            for p in players:
                if p['player_name'] == missing_player:
                    player_in_game = True
                    # Check if actually played (not DNP)
                    if p.get('minutes') and p['minutes'] not in ['0', '0:00', '', None]:
                        player_played = True
                    break
            
            if player_played:
                games_with_player.append(players)
            elif not player_in_game or (player_in_game and not player_played):
                games_without_player.append(players)
        
        if len(games_without_player) < 3:
            return {
                'error': 'Insufficient games without player',
                'games_without': len(games_without_player)
            }
        
        # Calculate team stats for both scenarios
        def calc_team_stats(games_list):
            team_points = []
            for game in games_list:
                total_points = sum(p['points'] for p in game)
                team_points.append(total_points)
            return {
                'avg_team_points': round(statistics.mean(team_points), 1) if team_points else 0,
                'games': len(games_list)
            }
        
        with_stats = calc_team_stats(games_with_player)
        without_stats = calc_team_stats(games_without_player)
        
        # Find beneficiaries (players who score more when key player is out)
        beneficiaries = []
        
        # Get unique players
        all_players = set()
        for game in games_without_player:
            for p in game:
                if p['player_name'] != missing_player:
                    all_players.add(p['player_name'])
        
        for player in all_players:
            with_player_stats = []
            without_player_stats = []
            
            for game in games_with_player:
                for p in game:
                    if p['player_name'] == player:
                        with_player_stats.append(p['points'])
            
            for game in games_without_player:
                for p in game:
                    if p['player_name'] == player:
                        without_player_stats.append(p['points'])
            
            if len(with_player_stats) >= 3 and len(without_player_stats) >= 3:
                avg_with = statistics.mean(with_player_stats)
                avg_without = statistics.mean(without_player_stats)
                difference = avg_without - avg_with
                
                if difference > 2:  # Significant increase
                    beneficiaries.append({
                        'player': player,
                        'avg_with_player': round(avg_with, 1),
                        'avg_without_player': round(avg_without, 1),
                        'increase': round(difference, 1),
                        'percent_increase': round((difference / avg_with) * 100, 1) if avg_with > 0 else 0
                    })
        
        # Sort beneficiaries by increase
        beneficiaries.sort(key=lambda x: x['increase'], reverse=True)
        
        return {
            'missing_player': missing_player,
            'team': team,
            'with_player': with_stats,
            'without_player': without_stats,
            'team_impact': {
                'points_difference': round(without_stats['avg_team_points'] - with_stats['avg_team_points'], 1),
                'description': f"Team scores {abs(without_stats['avg_team_points'] - with_stats['avg_team_points']):.1f} {'more' if without_stats['avg_team_points'] > with_stats['avg_team_points'] else 'less'} points without {missing_player}"
            },
            'beneficiaries': beneficiaries[:5],  # Top 5
            'sample_size': {
                'games_with': with_stats['games'],
                'games_without': without_stats['games']
            }
        }
