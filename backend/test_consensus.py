import math
from services.odds_service import _mad_filter, _select_price_for_point


def test_mad_filter_removes_outlier():
    points = [1.0, 1.5, 2.0, 10.0]
    filtered, removed = _mad_filter(points)
    assert removed == 1
    assert 10.0 not in filtered


def test_select_price_exact_match():
    samples = [
        {"point": -2.5, "price": -110},
        {"point": -2.5, "price": -105},
        {"point": -3.0, "price": -115},
    ]
    price = _select_price_for_point(samples, -2.5)
    assert math.isclose(price, -107.5, rel_tol=1e-6)


def test_select_price_closest_point():
    samples = [
        {"point": 2.0, "price": -110},
        {"point": 3.0, "price": -120},
    ]
    price = _select_price_for_point(samples, 2.6)
    assert price == -120
