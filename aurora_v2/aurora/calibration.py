"""Calibrating cost from fills instead of trusting a number someone typed.

The backtest assumes a cost per round trip. Until real fills exist, that number is
an assumption, and an assumption that is 3x too low is the most common way a
"profitable" strategy becomes a losing one in production.

The rule here is pre-registered, so it cannot be bent after seeing the result:
- fewer than 30 fills: the assumption stands and the report says it is uncalibrated
- 30 or more: the measured mean blends with the prior, weighted by sample size, so a
  handful of lucky fills cannot overwrite years of assumptions
- the blend only replaces the assumption when the mean is statistically clear of it
  (|t| >= 2), otherwise the assumption stands with an explicit warning

Slippage is signed the way a trader feels it: positive means worse than the decision
price, whether the order was a buy or a sell.
"""
from dataclasses import dataclass
from math import sqrt
from typing import Iterable, List, Optional, Sequence

MIN_OBSERVATIONS = 30
T_THRESHOLD = 2.0
PRIOR_WEIGHT = 30.0
BPS = 10_000.0


def slippage_bps(decision_price: float, fill_price: float, is_buy: bool = True) -> float:
    """Positive = paid worse than decided. A buy filled higher, or a sell filled lower."""
    if decision_price <= 0 or fill_price <= 0:
        raise ValueError("prices must be positive")
    raw = (fill_price - decision_price) / decision_price * BPS
    return raw if is_buy else -raw


def measure(fills: Iterable[tuple]) -> List[float]:
    """fills as (decision_price, fill_price, is_buy) -> signed bps list."""
    return [slippage_bps(d, f, b) for d, f, b in fills]


@dataclass(frozen=True)
class Calibration:
    n: int
    mean_bps: Optional[float]
    stderr_bps: Optional[float]
    t_stat: Optional[float]
    assumption_bps: float
    calibrated_bps: float
    confident: bool
    verdict: str

    def summary(self) -> str:
        if not self.n:
            return f"uncalibrated: 0 fills, keeping the {self.assumption_bps:.1f} bps assumption"
        base = (f"{self.n} fills, mean {self.mean_bps:+.1f} bps "
                f"(t {self.t_stat:+.2f}), using {self.calibrated_bps:.1f} bps")
        return base + ("" if self.confident else " [UNCONFIRMED: assumption dominates]")


def calibrate(observations: Sequence[float], assumption_bps: float = 10.0,
              prior_weight: float = PRIOR_WEIGHT) -> Calibration:
    obs = [float(x) for x in observations]
    n = len(obs)
    if n == 0:
        return Calibration(0, None, None, None, assumption_bps, assumption_bps, False, "uncalibrated")

    mean = sum(obs) / n
    if n > 1:
        var = sum((x - mean) ** 2 for x in obs) / (n - 1)
        stderr = sqrt(var / n)
        if stderr > 0:
            t_stat = (mean - assumption_bps) / stderr
        else:                       # every fill identical: distance is unambiguous
            t_stat = float("inf") if abs(mean - assumption_bps) > 1e-9 else 0.0
    else:
        stderr, t_stat = float("inf"), 0.0

    blended = (mean * n + assumption_bps * prior_weight) / (n + prior_weight)
    confident = n >= MIN_OBSERVATIONS and abs(t_stat) >= T_THRESHOLD
    used = blended if confident else max(assumption_bps, blended)
    verdict = ("measured cost differs from the assumption: adopt the blend"
               if confident else
               f"insufficient evidence ({n}/{MIN_OBSERVATIONS} fills or |t|<{T_THRESHOLD}): "
               "assumption kept, and raised if fills were worse")
    return Calibration(n, mean, stderr, t_stat, assumption_bps, used, confident, verdict)
