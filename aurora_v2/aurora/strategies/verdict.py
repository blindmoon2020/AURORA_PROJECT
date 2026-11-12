"""One place that decides whether a return series may be funded.

The DSR unit bug (annualised trial Sharpes passed into a per-period function)
appeared in four separate scripts, which is what happens when the same arithmetic
is rewritten by hand every time. This module is the single implementation.
"""
import math
from dataclasses import dataclass
from typing import Sequence

from ..stats import deflated_sharpe_ratio, t_p_value, t_stat, sharpe, max_drawdown

GATE_DSR = 0.95
GATE_T = 2.0


@dataclass(frozen=True)
class Verdict:
    sharpe: float
    t_stat: float
    p_value: float
    dsr: float
    max_dd_pct: float
    trials: int
    passed: bool
    reason: str


def funding_verdict(
    returns: Sequence[float],
    trial_sharpes: Sequence[float],
    periods_per_year: int = 252,
    trials_are_annualised: bool = True,
    gate_dsr: float = GATE_DSR,
    gate_t: float = GATE_T,
) -> Verdict:
    """Judge a return series against the funding gate, refusing unit ambiguity."""
    if len(returns) < 30:
        return Verdict(0.0, 0.0, 1.0, 0.0, 0.0, len(trial_sharpes), False,
                       "not enough observations to judge")
    scale = math.sqrt(periods_per_year) if trials_are_annualised else 1.0
    per_period = [s / scale for s in trial_sharpes]
    sr = sharpe(returns, periods_per_year)
    t = t_stat(returns)
    p = t_p_value(t, max(2, len(returns) - 1))
    dsr = float(deflated_sharpe_ratio(returns, per_period).get("dsr", 0.0))
    curve, eq = [1.0], 1.0
    for r in returns:
        eq *= 1.0 + r
        curve.append(eq)
    dd = max_drawdown(curve)[1]
    ok = dsr >= gate_dsr and t >= gate_t
    reason = ("passes the funding gate" if ok else
              f"fails: DSR {dsr:.3f} < {gate_dsr}" if dsr < gate_dsr else
              f"fails: t-stat {t:.2f} < {gate_t}")
    return Verdict(sr, t, p, dsr, dd, len(trial_sharpes), ok, reason)
