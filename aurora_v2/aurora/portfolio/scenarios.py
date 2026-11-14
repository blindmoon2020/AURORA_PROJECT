"""Named crises, reverse stress, and fat tails: the part of the audit that was still thin.

The first pass at stress testing (aurora/portfolio/stress.py) resampled our own returns.
That answers "how bad was a reordering of our history", which is a real question but a
small one: history contains no crisis in which every sleeve fell together, because we
have not lived through one yet. Institutions answer with three more tools, and this
module adds them:

  1. NAMED SCENARIOS - replay 2008, 2020, 2022 and the 2024 carry unwind against today's
     book, using the shocks those episodes actually delivered per asset class.
  2. REVERSE STRESS - instead of asking what we lose, ask how large a shock is needed to
     breach the limit. A book that breaks at 18% has no margin; one that survives 40% does.
  3. FAT TAILS - a uniform -20% assumes normality. Markets do not: a Student-t tail at the
     99th percentile is the honest version, and it is always worse than the Gaussian one.

The shocks below are round, public, and stated as assumptions. They are not precise
tick-by-tick replays, and calling them that would be the exact dishonesty this project
keeps auditing out of itself.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Sequence

# asset class -> (equity, bonds, gold, commodities, credit, crypto, cash)
SCENARIOS: Dict[str, Dict[str, float]] = {
    "۲۰۰۸ بحران مالی": {"equity": -0.38, "bonds": 0.05, "gold": 0.05,
                        "commodities": -0.36, "credit": -0.15, "crypto": -0.30, "fx": 0.0},
    "۲۰۲۰ کووید": {"equity": -0.34, "bonds": 0.08, "gold": 0.04,
                   "commodities": -0.45, "credit": -0.10, "crypto": -0.30, "fx": 0.0},
    "۲۰۲۲ شوک نرخ": {"equity": -0.25, "bonds": -0.17, "gold": -0.01,
                     "commodities": 0.16, "credit": -0.12, "crypto": -0.64, "fx": 0.02},
    "۲۰۲۴ بستن کری": {"equity": -0.08, "bonds": 0.02, "gold": -0.01,
                      "commodities": -0.05, "credit": -0.02, "crypto": -0.15, "fx": -0.01},
}
DEFAULT_CLASS_SHOCK = -0.25      # an unknown exposure is assumed to lose, not to be safe


@dataclass(frozen=True)
class ScenarioLoss:
    name: str
    loss_pct: float              # negative is a loss
    breaches_limit: bool
    worst_leg: str

    def line(self) -> str:
        return (f"{self.name}: {self.loss_pct:+.1f}% "
                f"{'— نقض حد' if self.breaches_limit else ''} (بدترین: {self.worst_leg})")


def class_of(symbol: str) -> str:
    """A deliberately rough classifier. Rough and declared beats precise and silent."""
    s = symbol.upper()
    if s in {"TLT", "IEF", "SHY", "BND", "AGG"}:
        return "bonds"
    if s in {"GLD", "IAU", "XAUUSD", "GC=F"}:
        return "gold"
    if s in {"DBC", "GSG", "CL=F", "ZC=F", "ZW=F", "NG=F"}:
        return "commodities"
    if s in {"BTC-USD", "ETH-USD"}:
        return "crypto"
    if s in {"HYG", "JNK", "LQD"}:
        return "credit"
    if s.endswith("=X") or s in {"EURUSD", "USDJPY"}:
        return "fx"
    return "equity"


def replay(weights: Dict[str, float], scenario: str,
           limit_pct: Optional[float] = None,
           shock_table: Optional[Dict[str, float]] = None) -> ScenarioLoss:
    """Mark the current book through one named crisis."""
    table = shock_table or SCENARIOS.get(scenario)
    if table is None:
        raise KeyError(f"unknown scenario: {scenario}")
    total, worst, worst_leg = 0.0, 0.0, ""
    for sym, w in weights.items():
        shock = table.get(class_of(sym), DEFAULT_CLASS_SHOCK)
        leg = w * shock
        total += leg
        if leg < worst:
            worst, worst_leg = leg, sym
    loss = total * 100.0
    return ScenarioLoss(scenario, loss,
                        breaches_limit=(limit_pct is not None and loss < -abs(limit_pct)),
                        worst_leg=worst_leg or "—")


def replay_all(weights: Dict[str, float], limit_pct: Optional[float] = None) -> list:
    return [replay(weights, name, limit_pct) for name in SCENARIOS]


def reverse_stress(weights: Dict[str, float], limit_pct: float,
                   lo: float = 0.0, hi: float = 1.0, tolerance: float = 1e-4) -> float:
    """How big a uniform shock is needed to breach the limit? Returns that shock, positive.

    Bisection, because the answer must be a number a risk committee can argue with, not a
    guess. If even a 100% loss does not breach (a nearly empty book), 1.0 is returned.
    """
    gross = sum(abs(w) for w in weights.values())
    if gross <= 0:
        return 1.0
    target = abs(limit_pct) / 100.0
    if gross * hi < target:
        return hi
    while hi - lo > tolerance:
        mid = (lo + hi) / 2
        if gross * mid < target:
            lo = mid
        else:
            hi = mid
    return hi


def tail_loss(weights: Dict[str, float], daily_vol: float = 0.01, horizon_days: int = 21,
              df: float = 3.0, quantile: float = 0.99) -> float:
    """Parametric Student-t tail: the loss size that a normal model would understate.

    df=3 is a fat tail calibrated to equity-like return series; lower df means fatter.
    """
    if weights is None:
        raise ValueError("weights required")
    gross = sum(abs(w) for w in weights.values())
    if gross <= 0:
        return 0.0
    sigma = daily_vol * (horizon_days ** 0.5)
    # Student-t quantile approximated from the normal quantile with the standard
    # variance correction; exact enough for a 99th percentile and honest about method.
    z = {0.95: 1.645, 0.99: 2.326, 0.999: 3.090}.get(quantile, 2.326)
    inflate = (df / (df - 2)) ** 0.5 if df > 2 else 2.0
    return -gross * sigma * z * inflate * 100.0


def margin_of_safety(weights: Dict[str, float], limit_pct: float) -> Dict[str, float]:
    """How much room the book has: the shock that breaks it versus each scenario."""
    return {"shock_to_breach_pct": reverse_stress(weights, limit_pct) * 100.0,
            "worst_scenario_pct": min(r.loss_pct for r in replay_all(weights))}


def crisis_exposure_cap(weights: Dict[str, float], limit_pct: float,
                        scenario: Optional[str] = None) -> Dict[str, float]:
    """The gross exposure at which the worst named crisis stays inside the limit.

    This is the number the audit produced and the book does not yet obey: a 130% gross
    book loses 49% in a 2008 replay against a 40% limit, so the cap is 0.82 of current
    exposure. Reported rather than applied, because scaling the strategy down is a mission
    decision about return, not a bug fix - and a rule adopted after seeing the stress test
    must be written down before the next session, not tuned to taste afterwards.
    """
    losses = [(r.name, r.loss_pct) for r in replay_all(weights)]
    if scenario is not None:
        losses = [(n, l) for n, l in losses if n == scenario]
    if not losses:
        raise KeyError(f"no scenario matched {scenario}")
    worst_name, worst_loss = min(losses, key=lambda kv: kv[1])
    gross = sum(abs(w) for w in weights.values())
    if worst_loss >= 0 or gross <= 0:
        return {"scale": 1.0, "cap_gross_pct": gross * 100.0,
                "binding_scenario": worst_name, "worst_loss_pct": worst_loss}
    needed = abs(limit_pct) / abs(worst_loss)
    scale = min(1.0, needed)
    return {"scale": scale, "cap_gross_pct": gross * 100.0 * scale,
            "binding_scenario": worst_name, "worst_loss_pct": worst_loss}
