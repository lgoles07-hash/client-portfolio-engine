"""Historical asset-class returns.

The bundled file (data/annual_returns.csv) holds APPROXIMATE calendar-year total
returns in PERCENT, entered from memory of published index figures:

    US Equity   ~ S&P 500 TR          Intl Equity ~ MSCI EAFE (net)
    REITs       ~ FTSE Nareit All Eq  US Bonds    ~ Bloomberg US Aggregate
    TIPS        ~ Bloomberg US TIPS   Cash        ~ 3-month T-bill

Verify against your data provider before quoting any number externally. To use
your own data, pass a CSV with the same columns (year index, returns in percent).
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
