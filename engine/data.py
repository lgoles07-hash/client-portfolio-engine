"""Historical asset-class returns.

data/annual_returns.csv holds calendar-year total returns in PERCENT for six ETF
proxies (SPY, EFA, VNQ, AGG, TIP, SHV). Rebuild it with `python3 fetch_data.py`;
data/SOURCE.txt records where and when it was downloaded. To use your own data,
pass a CSV with the same columns (year index, returns in percent).
"""
from pathlib import Path
import pandas as pd

ASSETS = ["US Equity", "Intl Equity", "REITs", "US Bonds", "TIPS", "Cash"]
DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "annual_returns.csv"


def load_returns(path=None) -> pd.DataFrame:
    """Return a DataFrame indexed by year with decimal returns (0.05 = 5%)."""
    df = pd.read_csv(path or DEFAULT_PATH, index_col="year")
    missing = [a for a in ASSETS if a not in df.columns]
    if missing:
        raise ValueError(f"Data file missing columns: {missing}")
    return df[ASSETS] / 100.0
