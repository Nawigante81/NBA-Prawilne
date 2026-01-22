"""
Unit tests for betting math functions.
"""
import pytest
from services.betting_math import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    expected_value,
    kelly_criterion,
    calculate_fair_odds,
    calculate_clv_spreads,
    calculate_clv_totals,
    calculate_clv_moneyline,
    remove_vig_two_way,
    calculate_parlay_odds,
    calculate_parlay_implied_probability
)


class TestOddsConversion:
    """Test odds conversion functions."""
    
    def test_american_to_decimal_positive(self):
        """Test converting positive American odds to decimal."""
        assert american_to_decimal(150) == 2.5
        assert american_to_decimal(100) == 2.0
        assert american_to_decimal(200) == 3.0
    
    def test_american_to_decimal_negative(self):
        """Test converting negative American odds to decimal."""
        assert abs(american_to_decimal(-110) - 1.909) < 0.01
        assert american_to_decimal(-200) == 1.5
        assert abs(american_to_decimal(-150) - 1.667) < 0.01
    
    def test_decimal_to_american_gte_2(self):
        """Test converting decimal >= 2.0 to American."""
        assert decimal_to_american(2.5) == 150
        assert decimal_to_american(2.0) == 100
        assert decimal_to_american(3.0) == 200
    
    def test_decimal_to_american_lt_2(self):
        """Test converting decimal < 2.0 to American."""
        assert abs(decimal_to_american(1.909) - (-110)) < 1
        assert decimal_to_american(1.5) == -200
        assert abs(decimal_to_american(1.667) - (-150)) < 1


class TestImpliedProbability:
    """Test implied probability calculations."""
    
    def test_implied_prob_american_positive(self):
        """Test implied probability from positive American odds."""
        prob = implied_probability(150, "american")
        assert abs(prob - 0.4) < 0.01
    
    def test_implied_prob_american_negative(self):
        """Test implied probability from negative American odds."""
        prob = implied_probability(-110, "american")
        assert abs(prob - 0.524) < 0.01
    
    def test_implied_prob_decimal(self):
        """Test implied probability from decimal odds."""
        prob = implied_probability(2.0, "decimal")
        assert prob == 0.5
        
        prob = implied_probability(2.5, "decimal")
        assert prob == 0.4


class TestExpectedValue:
    """Test expected value calculations."""
    
    def test_ev_positive(self):
        """Test positive EV calculation."""
        # If we think 60% chance but odds imply 50%, we have positive EV
        ev = expected_value(0.6, 100, "american", stake=1.0)
        assert ev > 0
    
    def test_ev_negative(self):
        """Test negative EV calculation."""
        # If we think 40% chance but odds imply 50%, we have negative EV
        ev = expected_value(0.4, 100, "american", stake=1.0)
        assert ev < 0
    
    def test_ev_zero(self):
        """Test zero EV calculation."""
        # If our estimate matches implied prob, EV should be near zero
        ev = expected_value(0.5, 100, "american", stake=1.0)
        assert abs(ev) < 0.01


class TestKellyCriterion:
    """Test Kelly Criterion calculations."""
    
    def test_kelly_with_edge(self):
        """Test Kelly with positive edge."""
        # 60% win prob at +100 odds should return positive stake
        stake = kelly_criterion(0.6, 100, "american", fraction=1.0, max_stake_pct=0.1)
        assert stake > 0
        assert stake <= 0.1
    
    def test_kelly_no_edge(self):
        """Test Kelly with no edge."""
        # 50% win prob at +100 odds should return zero stake
        stake = kelly_criterion(0.5, 100, "american", fraction=1.0, max_stake_pct=0.1)
        assert stake == 0
    
    def test_kelly_half_fraction(self):
        """Test half Kelly."""
        # Use values that won't hit the max cap
        full_kelly = kelly_criterion(0.55, 100, "american", fraction=1.0, max_stake_pct=1.0)
        half_kelly = kelly_criterion(0.55, 100, "american", fraction=0.5, max_stake_pct=1.0)
        
        assert half_kelly < full_kelly
        assert abs(half_kelly - full_kelly * 0.5) < 0.001
    
    def test_kelly_max_stake_cap(self):
        """Test Kelly respects max stake."""
        # Even with huge edge, should cap at max_stake_pct
        stake = kelly_criterion(0.9, 100, "american", fraction=1.0, max_stake_pct=0.03)
        assert stake <= 0.03


class TestFairOdds:
    """Test fair odds calculation."""
    
    def test_fair_odds_american(self):
        """Test fair American odds calculation."""
        odds = calculate_fair_odds(0.5, "american")
        assert odds == 100
        
        # 0.6 probability should give negative odds (favorite)
        odds = calculate_fair_odds(0.6, "american")
        assert odds < 0  # Should be around -150
        assert abs(odds - (-150)) < 10
    
    def test_fair_odds_decimal(self):
        """Test fair decimal odds calculation."""
        odds = calculate_fair_odds(0.5, "decimal")
        assert odds == 2.0
        
        odds = calculate_fair_odds(0.4, "decimal")
        assert odds == 2.5


class TestCLV:
    """Test Closing Line Value calculations."""
    
    def test_clv_spreads_favorite(self):
        """Test CLV for spread favorite."""
        # Bet at -7.5, closing line -8.5 => gained 1 point (good)
        clv = calculate_clv_spreads(-7.5, -8.5, is_favorite=True)
        assert clv == 1.0
        
        # Bet at -7.5, closing line -6.5 => lost 1 point (bad)
        clv = calculate_clv_spreads(-7.5, -6.5, is_favorite=True)
        assert clv == -1.0
    
    def test_clv_spreads_underdog(self):
        """Test CLV for spread underdog."""
        # Bet at +7.5, closing line +8.5 => gained 1 point (good)
        clv = calculate_clv_spreads(7.5, 8.5, is_favorite=False)
        assert clv == 1.0
        
        # Bet at +7.5, closing line +6.5 => lost 1 point (bad)
        clv = calculate_clv_spreads(7.5, 6.5, is_favorite=False)
        assert clv == -1.0
    
    def test_clv_totals_over(self):
        """Test CLV for Over."""
        # Bet Over 215.5, closing line 214.5 => gained 1 point (good)
        clv = calculate_clv_totals(215.5, 214.5, is_over=True)
        assert clv == 1.0
        
        # Bet Over 215.5, closing line 216.5 => lost 1 point (bad)
        clv = calculate_clv_totals(215.5, 216.5, is_over=True)
        assert clv == -1.0
    
    def test_clv_totals_under(self):
        """Test CLV for Under."""
        # Bet Under 215.5, closing line 216.5 => gained 1 point (good)
        clv = calculate_clv_totals(215.5, 216.5, is_over=False)
        assert clv == 1.0
    
    def test_clv_moneyline(self):
        """Test CLV for moneyline."""
        # Bet at +150, closing at +180 => got worse odds (bad)
        clv_prob, clv_price = calculate_clv_moneyline(150, 180, "american")
        assert clv_prob < 0  # Closing line implied lower probability
        assert clv_price == 30  # Price delta


class TestVigRemoval:
    """Test vig removal."""
    
    def test_remove_vig(self):
        """Test removing vig from two-way market."""
        # Typical -110/-110 market
        prob_a = implied_probability(-110, "american")
        prob_b = implied_probability(-110, "american")
        
        true_a, true_b = remove_vig_two_way(prob_a, prob_b)
        
        assert abs(true_a - 0.5) < 0.01
        assert abs(true_b - 0.5) < 0.01
        assert abs(true_a + true_b - 1.0) < 0.001


class TestParlays:
    """Test parlay calculations."""
    
    def test_parlay_odds_american(self):
        """Test parlay odds calculation with American odds."""
        # Two legs at +100 each
        parlay_odds = calculate_parlay_odds([100, 100], "american")
        assert abs(parlay_odds - 300) < 1  # Should be +300
    
    def test_parlay_odds_decimal(self):
        """Test parlay odds calculation with decimal odds."""
        # Two legs at 2.0 each
        parlay_odds = calculate_parlay_odds([2.0, 2.0], "decimal")
        assert parlay_odds == 4.0
    
    def test_parlay_implied_prob(self):
        """Test parlay implied probability."""
        # Two 50% legs should be 25% combined
        prob = calculate_parlay_implied_probability([100, 100], "american")
        assert abs(prob - 0.25) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
