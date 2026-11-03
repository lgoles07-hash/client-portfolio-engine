"""Client profile: the inputs an advisor collects at onboarding."""
from dataclasses import dataclass, asdict
import json

GOALS = ("growth", "retirement", "education", "income", "preservation")


@dataclass
class ClientProfile:
    name: str
    age: int
    horizon_years: int            # years until the money is needed (or drawdown period)
    goal: str                     # one of GOALS
    risk_tolerance: int           # 1 (very conservative) .. 5 (very aggressive), from questionnaire
    income_stability: int         # 1 (volatile/uncertain) .. 5 (very secure)
    liquidity_need_pct: float     # share of portfolio needed within ~3 years (0..1)
    max_tolerable_loss: float     # largest one-year decline the client says they can sit through (0..1)
    portfolio_value: float
    annual_contribution: float = 0.0

    def __post_init__(self):
        if self.goal not in GOALS:
            raise ValueError(f"goal must be one of {GOALS}")
        if not 18 <= self.age <= 100:
            raise ValueError("age must be 18-100")
        if self.horizon_years < 1:
            raise ValueError("horizon_years must be >= 1")
        for field in ("risk_tolerance", "income_stability"):
            if not 1 <= getattr(self, field) <= 5:
                raise ValueError(f"{field} must be 1-5")
        for field in ("liquidity_need_pct", "max_tolerable_loss"):
            if not 0 <= getattr(self, field) <= 1:
                raise ValueError(f"{field} must be between 0 and 1")
        if self.portfolio_value <= 0:
            raise ValueError("portfolio_value must be positive")

    @classmethod
    def from_json(cls, path):
        with open(path) as f:
            return cls(**json.load(f))

    def to_dict(self):
        return asdict(self)
