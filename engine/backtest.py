"""Backtesting and stress testing on annually rebalanced portfolios."""
import numpy as np
import pandas as pd

BENCH_60_40 = {"US Equity": 0.36, "Intl Equity": 0.24, "US Bonds": 0.40}

SCENARIOS = {
    "2008 Global Financial Crisis": [2008],
    "2020 calendar year (hides the March crash)": [2020],
    "2022 Rate shock (stocks and bonds down)": [2022],
    "2007-2009 Crisis cycle": [2007, 2008, 2009],
    "Full period": None,  # all available years
}


def portfolio_returns(weights: dict, returns: pd.DataFrame) -> pd.Series:
    """Annually rebalanced portfolio return for each year."""
    w = pd.Series(weights).reindex(returns.columns).fillna(0.0)
    if abs(w.sum() - 1) > 1e-6:
        raise ValueError(f"Weights sum to {w.sum():.4f}, expected 1")
    return (returns * w).sum(axis=1)


def total_return(r: pd.Series) -> float:
    return float((1 + r).prod() - 1)


def metrics(r: pd.Series, rf: pd.Series) -> dict:
    n = len(r)
    path = np.concatenate([[1.0], (1 + r).cumprod().values])
    drawdown = path / np.maximum.accumulate(path) - 1
    excess = r - rf
    return {
        "CAGR": path[-1] ** (1 / n) - 1,
        "Volatility": r.std(ddof=1) if n > 1 else float("nan"),
        "Worst year": r.min(),
        "Max drawdown": drawdown.min(),
        "Sharpe": excess.mean() / excess.std(ddof=1) if n > 2 and excess.std(ddof=1) > 0 else float("nan"),
    }


def stress_table(weights: dict, returns: pd.DataFrame, portfolio_value: float) -> pd.DataFrame:
    port = portfolio_returns(weights, returns)
    bench = portfolio_returns(BENCH_60_40, returns)
    rows = []
    for name, years in SCENARIOS.items():
        idx = returns.index if years is None else [y for y in years if y in returns.index]
        if len(idx) == 0:
            continue
        p, b = total_return(port.loc[idx]), total_return(bench.loc[idx])
        rows.append({"Scenario": name, "Portfolio": p, "60/40 benchmark": b,
                     "Dollar impact": p * portfolio_value})
    return pd.DataFrame(rows)


def growth_of(weights: dict, returns: pd.DataFrame, start=10_000) -> pd.Series:
    return start * (1 + portfolio_returns(weights, returns)).cumprod()
