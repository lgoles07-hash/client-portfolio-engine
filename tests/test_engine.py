"""Run with `python -m pytest` or simply `python tests/test_engine.py`."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import replace
from engine.allocate import build_allocation, compose
from engine.backtest import portfolio_returns, metrics
from engine.data import load_returns
from engine.profile import ClientProfile

R = load_returns()
BASE = ClientProfile("Test", 40, 25, "growth", 3, 4, 0.02, 0.60, 100_000)


def test_weights_sum_to_one_and_nonnegative():
    for eq in (0.10, 0.35, 0.55, 0.90):
        for cash in (0.02, 0.10, 0.25):
            w = compose(eq, cash)
            assert abs(sum(w.values()) - 1) < 1e-9
            assert min(w.values()) >= 0


def test_equity_increases_with_risk_tolerance():
    eq = [build_allocation(replace(BASE, risk_tolerance=t), R).equity_final for t in range(1, 6)]
    assert eq == sorted(eq) and eq[0] < eq[-1]


def test_short_horizon_caps_equity():
    a = build_allocation(replace(BASE, horizon_years=2, risk_tolerance=5), R)
    assert a.equity_final <= 0.20


def test_cash_covers_liquidity_need():
    a = build_allocation(replace(BASE, liquidity_need_pct=0.15), R)
    assert a.weights["Cash"] >= 0.15


def test_loss_guardrail_respected():
    p = replace(BASE, risk_tolerance=5, max_tolerable_loss=0.15)
    a = build_allocation(p, R)
    assert portfolio_returns(a.weights, R).min() >= -0.15 - 1e-9


def test_unattainable_loss_limit_is_flagged_not_hidden():
    p = replace(BASE, risk_tolerance=1, age=70, horizon_years=15, max_tolerable_loss=0.05)
    a = build_allocation(p, R)
    assert any("WARNING" in n for n in a.notes)


def test_max_drawdown_matches_hand_calc():
    import pandas as pd
    r = pd.Series([0.10, -0.20, 0.05, 0.30], index=[1, 2, 3, 4])
    m = metrics(r, pd.Series(0.0, index=r.index))
    # wealth: 1.0 -> 1.10 -> 0.88 -> 0.924 -> 1.2012; peak 1.10, trough 0.88
    assert abs(m["Max drawdown"] - (0.88 / 1.10 - 1)) < 1e-9
    assert abs(m["Worst year"] - (-0.20)) < 1e-9
    assert abs(m["CAGR"] - (1.2012 ** 0.25 - 1)) < 1e-9


def test_price_to_annual_return_conversion():
    import pandas as pd
    from fetch_data import annual_returns_from_prices
    idx = pd.to_datetime(["2006-12-29", "2007-06-30", "2007-12-31", "2008-12-31"])
    prices = pd.DataFrame({"A": [100.0, 105.0, 110.0, 99.0],
                           "B": [float("nan"), 50.0, 55.0, 66.0]}, index=idx)  # B is a "young" fund
    out = annual_returns_from_prices(prices, 2007, 2008)
    assert abs(out.loc[2007, "A"] - 10.0) < 1e-6
    assert abs(out.loc[2008, "A"] - (-10.0)) < 1e-6
    assert abs(out.loc[2007, "B"] - 10.0) < 1e-6    # base = first available price (50)
    assert abs(out.loc[2008, "B"] - 20.0) < 1e-6


def test_invalid_profile_rejected():
    try:
        replace(BASE, risk_tolerance=9)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
