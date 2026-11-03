"""Turn a ClientProfile into a target asset allocation.

Method (mirrors how advisors reason about suitability):
  1. Risk TOLERANCE  - willingness to take risk (questionnaire).
  2. Risk CAPACITY   - ability to take risk (horizon, age, income stability, liquidity).
  3. Blend, weighted 80/20 toward the LOWER of the two.
  4. Map the score to an equity target, adjust for goal, apply horizon caps.
  5. Reserve a cash bucket for near-term liquidity needs.
  6. Guardrail: shrink equity until the worst historical calendar year is within the
     client's stated maximum tolerable loss.
"""
from dataclasses import dataclass, field
from .backtest import portfolio_returns
from .profile import ClientProfile

GOAL_ADJUST = {"preservation": -0.10, "income": -0.05, "retirement": 0.0,
               "education": 0.0, "growth": 0.05}
# (max horizon in years, max equity allowed)
HORIZON_CAPS = [(2, 0.20), (5, 0.45), (10, 0.65)]
EQUITY_MIN, EQUITY_MAX, MIN_CASH = 0.10, 0.90, 0.02


@dataclass
class Allocation:
    weights: dict
    tolerance_score: float
    capacity_score: float
    risk_score: float
    equity_pre_guardrail: float
    equity_final: float
    notes: list = field(default_factory=list)


def tolerance_score(p: ClientProfile) -> float:
    return (p.risk_tolerance - 1) / 4 * 10


def capacity_score(p: ClientProfile) -> float:
    horizon = min(p.horizon_years, 30) / 30 * 10
    stability = (p.income_stability - 1) / 4 * 10
    liquidity = (1 - min(p.liquidity_need_pct / 0.30, 1)) * 10
    age = max(0.0, min(1.0, (75 - p.age) / 45)) * 10
    return 0.40 * horizon + 0.20 * stability + 0.25 * liquidity + 0.15 * age


def compose(equity: float, cash: float) -> dict:
    """Split an equity/cash decision into the six asset classes (weights sum to 1)."""
    equity = min(equity, 1 - cash)
    reits = 0.10 * equity
    core = equity - reits
    us, intl = 0.65 * core, 0.35 * core
    fixed = 1 - equity - cash
    tips, agg = 0.25 * fixed, 0.75 * fixed
    w = {"US Equity": us, "Intl Equity": intl, "REITs": reits,
         "US Bonds": agg, "TIPS": tips, "Cash": cash}
    w = {k: round(v, 2) for k, v in w.items()}
    biggest = max(w, key=w.get)  # absorb rounding residue in the largest holding
    w[biggest] = round(w[biggest] + (1 - sum(w.values())), 2)
    return w


def build_allocation(p: ClientProfile, returns) -> Allocation:
    notes = []
    tol, cap = tolerance_score(p), capacity_score(p)
    score = 0.8 * min(tol, cap) + 0.2 * max(tol, cap)
    if cap < tol - 1:
        notes.append(f"Capacity ({cap:.1f}) is below stated tolerance ({tol:.1f}); score pulled toward capacity.")
    elif tol < cap - 1:
        notes.append(f"Tolerance ({tol:.1f}) is below capacity ({cap:.1f}); score pulled toward tolerance so the client can stick with the plan.")

    equity = 0.15 + 0.75 * score / 10 + GOAL_ADJUST[p.goal]
    equity = min(EQUITY_MAX, max(EQUITY_MIN, equity))
    equity = round(equity / 0.05) * 0.05
    if GOAL_ADJUST[p.goal]:
        notes.append(f"Goal '{p.goal}' adjusts equity by {GOAL_ADJUST[p.goal]:+.0%}.")

    for max_years, cap_eq in HORIZON_CAPS:
        if p.horizon_years <= max_years:
            if equity > cap_eq:
                equity = cap_eq
                notes.append(f"Horizon of {p.horizon_years} years caps equity at {cap_eq:.0%}.")
            break

    cash = max(MIN_CASH, round(p.liquidity_need_pct, 2))
    if cash > MIN_CASH:
        notes.append(f"Cash set to {cash:.0%} to cover near-term withdrawals.")
    if equity > 1 - cash:
        equity = round(1 - cash, 2)
    pre_guardrail = round(equity, 2)

    def worst_year(eq):
        return portfolio_returns(compose(eq, cash), returns).min()

    # Cut equity only while each 5-pt cut buys a meaningful (>= 0.5 pt) improvement in the
    # worst year. If the worst year is driven by bonds (e.g. 2022), cutting equity is futile.
    while worst_year(equity) < -p.max_tolerable_loss and equity > EQUITY_MIN + 1e-9:
        candidate = round(equity - 0.05, 2)
        if worst_year(candidate) - worst_year(equity) < 0.005:
            break
        equity = candidate
    worst = worst_year(equity)
    if equity < pre_guardrail:
        notes.append(f"Loss guardrail: equity cut from {pre_guardrail:.0%} to {equity:.0%} "
                     f"(worst historical year now {worst:.1%}; client limit {p.max_tolerable_loss:.0%}).")
    if worst < -p.max_tolerable_loss:
        notes.append(f"WARNING: worst historical year is {worst:.1%}, beyond the client's "
                     f"{p.max_tolerable_loss:.0%} limit, and cutting equity further does not fix it "
                     f"(the loss comes from bonds, as in 2022). Discuss expectations with the client or "
                     f"consider a larger cash or short-duration bucket.")

    return Allocation(compose(equity, cash), tol, cap, score, pre_guardrail, equity, notes)
