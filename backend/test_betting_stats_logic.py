from services.betting_stats_service import BettingStatsService


def test_ats_result_sign_consistency():
    service = BettingStatsService()
    # Favorite with negative spread wins ATS if adjusted > opp
    assert service._ats_result(110, 100, -5.5) == "W"
    # Favorite fails ATS if adjusted < opp
    assert service._ats_result(100, 110, -5.5) == "L"
    # Push case
    assert service._ats_result(105, 100, -5.0) == "P"
