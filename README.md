# Client-Profile-to-Portfolio Engine

Takes a client's profile (age, goal, horizon, risk tolerance, liquidity needs, loss limit) and produces:

1. a **risk-scored target asset allocation**,
2. a **historical stress test** (2008, 2020, 2022, full period) against a 60/40 benchmark,
3. a formatted **Investment Policy Statement (IPS)** with an allocation/growth chart.

## Run it

```bash
pip install -r requirements.txt
python fetch_data.py                   # pull real ETF data and rebuild data/annual_returns.csv
python run.py                          # all clients in clients/
python run.py clients/alex_chen.json   # one client
python run.py --data my_returns.csv    # your own returns (percent, same columns as data/annual_returns.csv)
python tests/test_engine.py            # or: python -m pytest
```
Reports land in `output/` (one `.md` IPS and one `.png` per client).

## Method

| Step | Logic |
|---|---|
| Risk tolerance | Questionnaire score (1-5) rescaled to 0-10 |
| Risk capacity | Weighted: horizon 40%, income stability 20%, liquidity need 25%, age 15% |
| Blended score | 80% weight on the **lower** of tolerance and capacity |
| Equity target | 15% + 75% x score/10, adjusted for goal, then capped by horizon (<=2y: 20%, <=5y: 45%, <=10y: 65%) |
| Cash bucket | max(2%, near-term liquidity need) |
| Loss guardrail | Cut equity in 5-pt steps while it meaningfully lowers the worst historical year; if the client's loss limit still can't be met, say so rather than hide it |
| Asset-class split | 10% of equity to REITs, remainder 65/35 US/International; fixed income 75% aggregate bonds / 25% TIPS |

All weights, caps, and splits are named constants in `engine/allocate.py`. They are modeling choices to defend (and tweak) in an interview, not industry standards.

## Known limitations (be upfront about these)

- **Annual returns only.** Intra-year drawdowns (March 2020) are understated. Next step: monthly returns from the same ETF proxies.
- **ETF proxies, not indexes.** Returns come from SPY, EFA, VNQ, AGG, TIP and SHV (Yahoo Finance via `fetch_data.py`; see `data/SOURCE.txt`). They are net of fund expenses, so they run slightly below the underlying indexes.
- No fees, taxes, or trading costs; annual rebalancing assumed.
- The scoring weights are heuristic, not calibrated or validated.

## Extension ideas

Monte Carlo goal-probability module, tax-location (which assets in which accounts), ESG exclusions, Streamlit front-end, PDF export of the IPS.
