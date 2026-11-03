"""Rebuild data/annual_returns.csv from real market data.

Downloads dividend-adjusted prices for six ETF proxies and converts them to
calendar-year total returns (in percent).

    pip3 install yfinance pandas
    python3 fetch_data.py

Proxies (all trade since Jan 2007 or earlier, so 2007 is a full year):
    US Equity  SPY  (S&P 500)            Intl Equity  EFA  (MSCI EAFE)
    REITs      VNQ  (US REITs)           US Bonds     AGG  (US Aggregate Bond)
    TIPS       TIP  (US TIPS)            Cash         SHV  (0-1yr Treasuries)

Caveat: ETF returns are net of fund expenses, so they run slightly below the
underlying indexes. SHV's first trading day was in Jan 2007, so its 2007 figure
covers almost, not exactly, the full year.
"""
from datetime import date
from pathlib import Path
import pandas as pd

PROXIES = {"US Equity": "SPY", "Intl Equity": "EFA", "REITs": "VNQ",
           "US Bonds": "AGG", "TIPS": "TIP", "Cash": "SHV"}
START_YEAR = 2007
HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "annual_returns.csv"
SOURCE_NOTE = HERE / "data" / "SOURCE.txt"


def annual_returns_from_prices(prices: pd.DataFrame, start_year: int, last_year: int) -> pd.DataFrame:
    """Calendar-year returns in percent from a DataFrame of adjusted prices (DatetimeIndex)."""
    prices = prices.sort_index().dropna(how="all")
    year_end = prices.groupby(prices.index.year).last()
    prior = year_end.shift(1)
    for col in prices.columns:  # fund younger than the window: use its first price as the base
        first_year = year_end[col].first_valid_index()
        if pd.isna(prior.loc[first_year, col]):
            prior.loc[first_year, col] = prices[col].dropna().iloc[0]
    rets = (year_end / prior - 1) * 100
    rets = rets.loc[start_year:last_year].round(2)
    rets.index.name = "year"
    return rets


def main():
    import yfinance as yf  # imported here so the maths above can be tested offline

    last_year = date.today().year - 1  # only complete calendar years
    raw = yf.download(list(PROXIES.values()), start=f"{START_YEAR - 1}-12-01",
                      end=f"{last_year + 1}-01-10", auto_adjust=True, progress=False)
    prices = raw["Close"][list(PROXIES.values())]
    prices.columns = list(PROXIES.keys())
    rets = annual_returns_from_prices(prices, START_YEAR, last_year)
    if rets.isna().any().any():
        raise SystemExit(f"Missing data, nothing written:\n{rets[rets.isna().any(axis=1)]}")
    OUT.parent.mkdir(exist_ok=True)
    rets.to_csv(OUT)
    SOURCE_NOTE.write_text(
        f"Calendar-year total returns (%), {START_YEAR}-{last_year}.\n"
        f"Source: Yahoo Finance dividend-adjusted prices via yfinance, downloaded {date.today()}.\n"
        f"Proxies: {', '.join(f'{k}={v}' for k, v in PROXIES.items())}.\n"
        "ETF returns are net of fund expenses.\n")
    print(rets.to_string())
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
