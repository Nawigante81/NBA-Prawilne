"""
Value Board Service - Generates expected value calculations for upcoming games.
"""

from datetime import date, datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, func, desc
from sqlalchemy.orm import Session

from db import get_db
from models import Game, TeamGameStats, ValueBet, ValueBoard
from settings import HOME_COURT_ADVANTAGE, KELLY_FRACTION
from services import betting_math
from services.odds_service import get_consensus_line


def get_team_recent_stats(
    db: Session,
    team_id: int,
    n_games: int = 10
) -> Optional[dict]:
    """
    Get aggregated stats for a team's last N games.
    
    Returns dict with: off_rtg, def_rtg, pace, avg_pts, games_count
    """
    stmt = (
        select(
            func.avg(TeamGameStats.off_rtg).label('off_rtg'),
            func.avg(TeamGameStats.def_rtg).label('def_rtg'),
            func.avg(TeamGameStats.pace).label('pace'),
            func.avg(TeamGameStats.pts).label('avg_pts'),
            func.count(TeamGameStats.id).label('games_count')
        )
        .join(Game, TeamGameStats.game_id == Game.id)
        .where(
            and_(
                TeamGameStats.team_id == team_id,
                Game.status == 'Final'
            )
        )
        .order_by(desc(Game.game_date))
        .limit(n_games)
    )
    
    result = db.execute(stmt).first()
    
    if not result or result.games_count < 5:
        return None
    
    return {
        'off_rtg': float(result.off_rtg or 0),
        'def_rtg': float(result.def_rtg or 0),
        'pace': float(result.pace or 0),
        'avg_pts': float(result.avg_pts or 0),
        'games_count': int(result.games_count)
    }


def compute_model_probability(
    db: Session,
    game_id: int,
    market_type: str,
    team: Optional[str] = None
) -> Optional[float]:
    """
    Compute model probability for a game/market combination.
    
    Args:
        db: Database session
        game_id: Game ID
        market_type: 'spread', 'total', or 'h2h'
        team: 'home' or 'away' (required for spread and h2h)
    
    Returns:
        Probability between 0 and 1, or None if insufficient data
    """
    game = db.get(Game, game_id)
    if not game:
        return None
    
    home_stats = get_team_recent_stats(db, game.home_team_id)
    away_stats = get_team_recent_stats(db, game.away_team_id)
    
    if not home_stats or not away_stats:
        return None
    
    if market_type == 'spread':
        home_net_rtg = home_stats['off_rtg'] - home_stats['def_rtg']
        away_net_rtg = away_stats['off_rtg'] - away_stats['def_rtg']
        
        home_advantage = home_net_rtg - away_net_rtg + HOME_COURT_ADVANTAGE
        
        spread_std = 12.0
        z_score = home_advantage / spread_std
        
        home_prob = betting_math.normal_cdf(z_score)
        
        return home_prob if team == 'home' else (1 - home_prob)
    
    elif market_type == 'total':
        avg_pace = (home_stats['pace'] + away_stats['pace']) / 2
        avg_off = (home_stats['off_rtg'] + away_stats['off_rtg']) / 2
        
        estimated_total = (avg_off * avg_pace) / 100
        
        total_std = 12.0
        
        return 0.5
    
    elif market_type == 'h2h':
        home_prob = compute_model_probability(db, game_id, 'spread', 'home')
        
        if team == 'home':
            return home_prob
        else:
            return 1 - home_prob if home_prob else None
    
    return None


def generate_value_bet(
    db: Session,
    game_id: int,
    market_type: str,
    team: str,
    selection: str,
    line: float,
    price: int
) -> Optional[ValueBet]:
    """
    Generate a single value bet with EV and Kelly calculations.
    
    Args:
        db: Database session
        game_id: Game ID
        market_type: 'spread', 'total', or 'h2h'
        team: 'home' or 'away'
        selection: Description of the bet (e.g., "Lakers -5.5")
        line: The line value (spread, total, or moneyline)
        price: American odds (e.g., -110)
    
    Returns:
        ValueBet object or None if insufficient data
    """
    model_prob = compute_model_probability(db, game_id, market_type, team)
    
    if model_prob is None:
        return None
    
    implied_prob = betting_math.implied_probability(price)
    edge_prob = model_prob - implied_prob
    
    ev = betting_math.expected_value(model_prob, price)
    
    kelly = betting_math.kelly_criterion(model_prob, price)
    kelly_fraction = kelly * KELLY_FRACTION
    
    game = db.get(Game, game_id)
    
    return ValueBet(
        game_id=game_id,
        game_date=game.game_date,
        home_team=game.home_team_abbr,
        away_team=game.away_team_abbr,
        market_type=market_type,
        team=team,
        selection=selection,
        line=line,
        price=price,
        model_prob=round(model_prob, 4),
        implied_prob=round(implied_prob, 4),
        edge_prob=round(edge_prob, 4),
        ev=round(ev, 4),
        kelly_fraction=round(kelly_fraction, 4),
        confidence='high' if abs(edge_prob) > 0.05 else 'medium' if abs(edge_prob) > 0.02 else 'low'
    )


def compute_value_board_for_date(
    db: Session,
    target_date: date
) -> List[ValueBet]:
    """
    Generate value board for all games on a specific date.
    
    Args:
        db: Database session
        target_date: Date to generate value board for
    
    Returns:
        List of ValueBet objects sorted by EV descending
    """
    stmt = select(Game).where(
        and_(
            Game.game_date == target_date,
            Game.status.in_(['Scheduled', 'Not Started'])
        )
    )
    
    games = db.execute(stmt).scalars().all()
    
    value_bets = []
    
    for game in games:
        for market_type in ['spread', 'h2h', 'total']:
            consensus = get_consensus_line(db, game.id, market_type, cutoff=None)
            
            if not consensus:
                continue
            
            if market_type == 'spread':
                home_line = consensus['home_line']
                away_line = consensus['away_line']
                home_price = consensus['home_price']
                away_price = consensus['away_price']
                
                home_bet = generate_value_bet(
                    db, game.id, market_type, 'home',
                    f"{game.home_team_abbr} {home_line:+.1f}",
                    home_line, home_price
                )
                if home_bet:
                    value_bets.append(home_bet)
                
                away_bet = generate_value_bet(
                    db, game.id, market_type, 'away',
                    f"{game.away_team_abbr} {away_line:+.1f}",
                    away_line, away_price
                )
                if away_bet:
                    value_bets.append(away_bet)
            
            elif market_type == 'h2h':
                home_price = consensus['home_price']
                away_price = consensus['away_price']
                
                home_bet = generate_value_bet(
                    db, game.id, market_type, 'home',
                    f"{game.home_team_abbr} ML",
                    0, home_price
                )
                if home_bet:
                    value_bets.append(home_bet)
                
                away_bet = generate_value_bet(
                    db, game.id, market_type, 'away',
                    f"{game.away_team_abbr} ML",
                    0, away_price
                )
                if away_bet:
                    value_bets.append(away_bet)
            
            elif market_type == 'total':
                total_line = consensus.get('total_line', 0)
                over_price = consensus.get('over_price', -110)
                under_price = consensus.get('under_price', -110)
                
                over_bet = generate_value_bet(
                    db, game.id, market_type, 'total',
                    f"Over {total_line}",
                    total_line, over_price
                )
                if over_bet:
                    value_bets.append(over_bet)
                
                under_bet = generate_value_bet(
                    db, game.id, market_type, 'total',
                    f"Under {total_line}",
                    total_line, under_price
                )
                if under_bet:
                    value_bets.append(under_bet)
    
    value_bets.sort(key=lambda x: x.ev, reverse=True)
    
    return value_bets


def get_value_board_today(db: Session) -> ValueBoard:
    """
    Get value board for today's games.
    
    Returns:
        ValueBoard model with today's value bets
    """
    today = date.today()
    value_bets = compute_value_board_for_date(db, today)
    
    return ValueBoard(
        generated_at=datetime.now(),
        game_date=today,
        bets=value_bets,
        total_bets=len(value_bets)
    )
