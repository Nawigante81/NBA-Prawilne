"""
Betting mathematics: EV, Kelly Criterion, odds conversion, etc.
All core betting math functions for the platform.
"""
import math
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def american_to_decimal(american_odds: float) -> float:
    """
    Convert American odds to decimal odds.
    
    Args:
        american_odds: American odds (e.g., -110, +150)
    
    Returns:
        Decimal odds (e.g., 1.91, 2.50)
    """
    if american_odds > 0:
        return (american_odds / 100.0) + 1.0
    else:
        return (100.0 / abs(american_odds)) + 1.0


def decimal_to_american(decimal_odds: float) -> float:
    """
    Convert decimal odds to American odds.
    
    Args:
        decimal_odds: Decimal odds (e.g., 1.91, 2.50)
    
    Returns:
        American odds (e.g., -110, +150)
    """
    if decimal_odds >= 2.0:
        return (decimal_odds - 1.0) * 100.0
    else:
        return -100.0 / (decimal_odds - 1.0)


def implied_probability(odds: float, odds_format: str = "american") -> float:
    """
    Calculate implied probability from odds.
    
    Args:
        odds: Odds value
        odds_format: "american" or "decimal"
    
    Returns:
        Implied probability (0-1)
    """
    if odds_format == "decimal":
        return 1.0 / odds
    elif odds_format == "american":
        decimal = american_to_decimal(odds)
        return 1.0 / decimal
    else:
        raise ValueError(f"Unsupported odds format: {odds_format}")


def expected_value(
    model_probability: float, 
    odds: float, 
    odds_format: str = "american",
    stake: float = 1.0
) -> float:
    """
    Calculate expected value (EV) of a bet.
    
    Args:
        model_probability: Your estimated win probability (0-1)
        odds: Bookmaker odds
        odds_format: "american" or "decimal"
        stake: Bet size (default 1.0 for percentage)
    
    Returns:
        Expected value (positive = +EV, negative = -EV)
    """
    if odds_format == "american":
        decimal_odds = american_to_decimal(odds)
    else:
        decimal_odds = odds
    
    # EV = (probability * profit) - (1 - probability) * stake
    profit_if_win = (decimal_odds - 1.0) * stake
    loss_if_lose = stake
    
    ev = (model_probability * profit_if_win) - ((1 - model_probability) * loss_if_lose)
    return ev


def kelly_criterion(
    model_probability: float,
    odds: float,
    odds_format: str = "american",
    fraction: float = 1.0,
    max_stake_pct: float = 0.03
) -> float:
    """
    Calculate Kelly Criterion stake size.
    
    Args:
        model_probability: Your estimated win probability (0-1)
        odds: Bookmaker odds
        odds_format: "american" or "decimal"
        fraction: Fraction of Kelly to use (0.5 = half Kelly, 1.0 = full Kelly)
        max_stake_pct: Maximum stake as percentage of bankroll (default 3%)
    
    Returns:
        Recommended stake as percentage of bankroll (0-max_stake_pct)
    """
    if odds_format == "american":
        decimal_odds = american_to_decimal(odds)
    else:
        decimal_odds = odds
    
    # Kelly formula: f = (bp - q) / b
    # where b = decimal_odds - 1, p = win probability, q = lose probability
    b = decimal_odds - 1.0
    p = model_probability
    q = 1.0 - p
    
    # Only bet if there's an edge
    if p * b <= q:
        return 0.0
    
    kelly_pct = ((b * p) - q) / b
    
    # Apply fraction (e.g., half Kelly)
    fractional_kelly = kelly_pct * fraction
    
    # Clamp to max stake
    final_stake = max(0.0, min(fractional_kelly, max_stake_pct))
    
    return final_stake


def calculate_fair_odds(probability: float, odds_format: str = "american") -> float:
    """
    Calculate fair odds from a probability (no vig).
    
    Args:
        probability: True win probability (0-1)
        odds_format: "american" or "decimal"
    
    Returns:
        Fair odds in requested format
    """
    if probability <= 0 or probability >= 1:
        raise ValueError("Probability must be between 0 and 1")
    
    decimal_odds = 1.0 / probability
    
    if odds_format == "decimal":
        return decimal_odds
    elif odds_format == "american":
        return decimal_to_american(decimal_odds)
    else:
        raise ValueError(f"Unsupported odds format: {odds_format}")


def calculate_clv_spreads(
    bet_line: float,
    closing_line: float,
    is_favorite: bool
) -> float:
    """
    Calculate Closing Line Value (CLV) for spreads.
    
    Args:
        bet_line: Line you bet at (e.g., -7.5)
        closing_line: Closing line (e.g., -8.5)
        is_favorite: True if betting the favorite
    
    Returns:
        CLV in points (positive = good, negative = bad)
    """
    if is_favorite:
        # For favorite: if closing line moves MORE negative, that's good
        # e.g., bet at -7.5, close at -8.5 => CLV = +1.0
        clv = bet_line - closing_line
    else:
        # For underdog: if closing line moves MORE positive, that's good
        # e.g., bet at +7.5, close at +8.5 => CLV = +1.0
        clv = closing_line - bet_line
    
    return clv


def calculate_clv_totals(
    bet_line: float,
    closing_line: float,
    is_over: bool
) -> float:
    """
    Calculate Closing Line Value (CLV) for totals.
    
    Args:
        bet_line: Line you bet at (e.g., 215.5)
        closing_line: Closing line (e.g., 214.5)
        is_over: True if betting Over
    
    Returns:
        CLV in points (positive = good, negative = bad)
    """
    if is_over:
        # For Over: if closing line moves LOWER, that's good
        # e.g., bet Over 215.5, close at 214.5 => CLV = +1.0
        clv = bet_line - closing_line
    else:
        # For Under: if closing line moves HIGHER, that's good
        # e.g., bet Under 215.5, close at 216.5 => CLV = +1.0
        clv = closing_line - bet_line
    
    return clv


def calculate_clv_moneyline(
    bet_odds: float,
    closing_odds: float,
    odds_format: str = "american"
) -> Tuple[float, float]:
    """
    Calculate Closing Line Value (CLV) for moneyline.
    
    Args:
        bet_odds: Odds you bet at
        closing_odds: Closing odds
        odds_format: "american" or "decimal"
    
    Returns:
        Tuple of (clv_probability_delta, clv_price_delta)
    """
    bet_prob = implied_probability(bet_odds, odds_format)
    closing_prob = implied_probability(closing_odds, odds_format)
    
    # Positive CLV means closing line had LOWER implied probability
    clv_prob = closing_prob - bet_prob
    
    # Price delta
    if odds_format == "american":
        clv_price = closing_odds - bet_odds
    else:
        clv_price = closing_odds - bet_odds
    
    return clv_prob, clv_price


def remove_vig_two_way(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """
    Remove vig from two-way market to get true probabilities.
    
    Args:
        prob_a: Implied probability of outcome A
        prob_b: Implied probability of outcome B
    
    Returns:
        Tuple of (true_prob_a, true_prob_b)
    """
    total = prob_a + prob_b
    if total <= 1.0:
        # No vig or already no-vig
        return prob_a, prob_b
    
    # Normalize by total
    true_a = prob_a / total
    true_b = prob_b / total
    
    return true_a, true_b


def calculate_parlay_odds(odds_list: list, odds_format: str = "american") -> float:
    """
    Calculate combined odds for a parlay.
    
    Args:
        odds_list: List of individual odds
        odds_format: "american" or "decimal"
    
    Returns:
        Combined parlay odds in same format
    """
    if not odds_list:
        raise ValueError("odds_list cannot be empty")
    
    # Convert all to decimal
    decimal_odds_list = []
    for odds in odds_list:
        if odds_format == "american":
            decimal_odds_list.append(american_to_decimal(odds))
        else:
            decimal_odds_list.append(odds)
    
    # Multiply all together
    combined_decimal = 1.0
    for decimal_odds in decimal_odds_list:
        combined_decimal *= decimal_odds
    
    # Convert back if needed
    if odds_format == "american":
        return decimal_to_american(combined_decimal)
    else:
        return combined_decimal


def calculate_parlay_implied_probability(odds_list: list, odds_format: str = "american") -> float:
    """
    Calculate implied probability of a parlay.
    
    Args:
        odds_list: List of individual odds
        odds_format: "american" or "decimal"
    
    Returns:
        Implied probability of all legs hitting (0-1)
    """
    parlay_odds = calculate_parlay_odds(odds_list, odds_format)
    return implied_probability(parlay_odds, odds_format)
