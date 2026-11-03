"""Generate the Investment Policy Statement (Markdown) and a summary chart."""
from datetime import date
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from .allocate import Allocation
from .backtest import (BENCH_60_40, growth_of, metrics, portfolio_returns,
                       stress_table)
from .profile import ClientProfile

BENCHMARKS = {"US Equity": "S&P 500 TR", "Intl Equity": "MSCI EAFE (net)",
              "REITs": "FTSE Nareit All Equity", "US Bonds": "Bloomberg US Aggregate",
              "TIPS": "Bloomberg US TIPS", "Cash": "3-month T-bill"}
RANGE_PTS = {"US Equity": 0.05, "Intl Equity": 0.05, "REITs": 0.03,
             "US Bonds": 0.05, "TIPS": 0.03, "Cash": 0.02}
COLORS = ["#1f4e79", "#2e75b6", "#9dc3e6", "#548235", "#a9d18e", "#bfbfbf"]

GOAL_TEXT = {
    "growth": "Long-term capital appreciation",
    "retirement": "Accumulate and sustain assets for retirement",
    "education": "Fund future education expenses",
    "income": "Generate sustainable portfolio income with moderate growth",
    "preservation": "Preserve capital with modest real growth",
}


def _slug(name: str) -> str:
    return "".join(c.lower() if c.isalnum() else "_" for c in name).strip("_")


def make_chart(p: ClientProfile, alloc: Allocation, returns, path: Path):
    shown = {k: v for k, v in alloc.weights.items() if v > 0}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.pie(shown.values(), labels=[f"{k}\n{v:.0%}" for k, v in shown.items()],
           colors=COLORS[:len(shown)], startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"))
    a1.set_title("Target allocation")
    g = growth_of(alloc.weights, returns)
    b = growth_of(BENCH_60_40, returns)
    a2.plot(g.index, g.values, color="#1f4e79", lw=2, label="Recommended portfolio")
    a2.plot(b.index, b.values, color="#7f7f7f", lw=1.6, ls="--", label="60/40 benchmark")
    a2.set_title(f"Growth of $10,000 ({returns.index[0]}-{returns.index[-1]})")
    a2.yaxis.set_major_formatter(lambda x, _: f"${x:,.0f}")
    a2.xaxis.set_major_locator(MaxNLocator(integer=True))
    a2.legend(frameon=False)
    a2.spines[["top", "right"]].set_visible(False)
    fig.suptitle(p.name, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def build_ips(p: ClientProfile, alloc: Allocation, returns, chart_name: str) -> str:
    w = alloc.weights
    port = portfolio_returns(w, returns)
    bench = portfolio_returns(BENCH_60_40, returns)
    rf = returns["Cash"]
    m_p, m_b = metrics(port, rf), metrics(bench, rf)
    stress = stress_table(w, returns, p.portfolio_value)

    L = []
    add = L.append
    add(f"# Investment Policy Statement: {p.name}")
    add(f"*Prepared {date.today():%B %d, %Y}. Illustrative model output, not investment advice.*\n")
    add(f"![Allocation and growth]({chart_name})\n")

    add("## 1. Client summary")
    add(f"- **Age:** {p.age}  |  **Time horizon:** {p.horizon_years} years")
    add(f"- **Portfolio value:** ${p.portfolio_value:,.0f}  |  **Annual contribution:** ${p.annual_contribution:,.0f}")
    add(f"- **Primary objective:** {GOAL_TEXT[p.goal]}")
    add(f"- **Near-term liquidity need (next ~3 years):** {p.liquidity_need_pct:.0%} of portfolio")
    add(f"- **Maximum one-year loss the client can tolerate:** {p.max_tolerable_loss:.0%}\n")

    add("## 2. Risk profile")
    add("| Measure | Score (0-10) |\n|---|---|")
    add(f"| Risk tolerance (willingness) | {alloc.tolerance_score:.1f} |")
    add(f"| Risk capacity (ability) | {alloc.capacity_score:.1f} |")
    add(f"| **Blended risk score** (80% weight on the lower) | **{alloc.risk_score:.1f}** |\n")
    add("**How the recommendation was reached:**")
    for n in alloc.notes or ["No overrides applied; allocation follows directly from the blended risk score."]:
        add(f"- {n}")
    add("")

    add("## 3. Strategic asset allocation")
    add("| Asset class | Target | Range | Benchmark index |\n|---|---|---|---|")
    for k, v in w.items():
        lo, hi = max(0, v - RANGE_PTS[k]), min(1, v + RANGE_PTS[k])
        add(f"| {k} | {v:.0%} | {lo:.0%} - {hi:.0%} | {BENCHMARKS[k]} |")
    add(f"| **Total equity** | **{alloc.equity_final:.0%}** | | |\n")

    add("## 4. Rebalancing and cash-flow policy")
    add("- Review at least annually; rebalance when any asset class moves outside its range.")
    add("- Direct new contributions to underweight asset classes first to limit trading and taxes.")
    add("- Fund withdrawals from overweight classes and the cash bucket before selling underweights.")
    add("- Reassess the plan after any major life event (job change, inheritance, health, retirement date).\n")

    add(f"## 5. Historical stress tests ({returns.index[0]}-{returns.index[-1]})")
    add("| Scenario | Portfolio | 60/40 benchmark | Dollar impact |\n|---|---|---|---|")
    for _, r in stress.iterrows():
        add(f"| {r['Scenario']} | {r['Portfolio']:.1%} | {r['60/40 benchmark']:.1%} | {'-' if r['Dollar impact'] < 0 else ''}${abs(r['Dollar impact']):,.0f} |")
    add("")
    add("| Metric (full period) | Portfolio | 60/40 benchmark |\n|---|---|---|")
    for k in ("CAGR", "Volatility", "Worst year", "Max drawdown"):
        add(f"| {k} | {m_p[k]:.1%} | {m_b[k]:.1%} |")
    add(f"| Sharpe ratio | {m_p['Sharpe']:.2f} | {m_b['Sharpe']:.2f} |\n")

    add("## 6. Important limitations")
    add("- Backtests use **annual** returns, so intra-year drawdowns (e.g. March 2020) are understated.")
    add("- Past performance does not predict future results; the model assumes annual rebalancing and no fees, taxes, or trading costs.")
    add("- Historical data in this repo is approximate; verify against a licensed data source before relying on it.")
    add("- Questionnaire-based scoring is a starting point for an advisor conversation, not a substitute for it.\n")
    return "\n".join(L)


def write_report(p: ClientProfile, alloc: Allocation, returns, outdir) -> Path:
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    slug = _slug(p.name)
    chart = f"{slug}_summary.png"
    make_chart(p, alloc, returns, outdir / chart)
    md = outdir / f"{slug}_IPS.md"
    md.write_text(build_ips(p, alloc, returns, chart), encoding="utf-8")
    return md
