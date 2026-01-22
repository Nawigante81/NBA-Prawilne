"""
NBA Betting Analytics Backend - Betting Math
Calculations for implied probability, EV, Kelly criterion, etc.
"""
import logging

logger = logging.getLogger(__name__)


def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1


def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds to American odds"""
    if decimal_odds >= 2.0:
        return (decimal_odds - 1) * 100
    else:
        return -100 / (decimal_odds - 1)


def implied_probability(odds: float, odds_format: str = "decimal") -> float:
    """
    Calculate implied probability from odds
    
    Args:
        odds: Odds value
        odds_format: "american" or "decimal"
    
    Returns:
        Implied probability (0 to 1)
    """
    if odds_format == "american":
        decimal_odds = american_to_decimal(odds)
    else:
        decimal_odds = odds
    
    return 1.0 / decimal_odds


def expected_value(win_prob: float, odds: float, stake: float = 1.0, odds_format: str = "decimal") -> float:
    """
    Calculate expected value of a bet
    
    Args:
        win_prob: True probability of winning (0 to 1)
        odds: Odds offered
        stake: Bet stake (default 1.0)
        odds_format: "american" or "decimal"
    
    Returns:
        Expected value
    """
    if odds_format == "american":
        decimal_odds = american_to_decimal(odds)
    else:
        decimal_odds = odds
    
    win_amount = (decimal_odds - 1) * stake
    lose_amount = stake
    
    ev = (win_prob * win_amount) - ((1 - win_prob) * lose_amount)
    
    return ev


def kelly_criterion(win_prob: float, odds: float, fraction: float = 1.0, odds_format: str = "decimal") -> float:
    """
    Calculate Kelly criterion stake
    
    Args:
        win_prob: True probability of winning (0 to 1)
        odds: Odds offered
        fraction: Kelly fraction (0.5 for half Kelly, 1.0 for full Kelly)
        odds_format: "american" or "decimal"
    
    Returns:
        Optimal stake as fraction of bankroll (e.g., 0.05 = 5%)
    """
    if odds_format == "american":
        decimal_odds = american_to_decimal(odds)
    else:
        decimal_odds = odds
    
    b = decimal_odds - 1
    p = win_prob
    q = 1 - win_prob
    
    if b <= 0:
        return 0.0
    
    kelly = (b * p - q) / b
    kelly = max(0.0, kelly * fraction)
    
    return kelly


def calculate_edge(true_prob: float, implied_prob: float) -> float:
    """Calculate edge as difference between true and implied probability"""
    return true_prob - implied_prob


def calculate_clv(bet_line: float, closing_line: float, market_type: str = "spread") -> float:
    """
    Calculate Closing Line Value (CLV)
    
    CLV measures how much better your bet line was compared to the closing line.
    Positive CLV indicates you got a better price than the market closing price.
    
    Args:
        bet_line: The line/odds at which you placed the bet
        closing_line: The line/odds at market close (game start)
        market_type: Type of market ("spread", "totals", or other)
    
    Returns:
        CLV value:
        - For spread: positive means you got a more favorable spread
          (e.g., +3.5 vs +3.0 closing = +0.5 CLV)
        - For totals: absolute difference (any movement from your bet)
        - For other markets: 0.0 (not applicable)
    
    Example:
        >>> calculate_clv(3.5, 3.0, "spread")  # You got +3.5, closed at +3.0
        0.5
        >>> calculate_clv(220.5, 218.5, "totals")  # Line moved 2 points
        2.0
    """
    if market_type == "spread":
        return bet_line - closing_line
    elif market_type == "totals":
        return abs(bet_line - closing_line)
    else:
        return 0.0
