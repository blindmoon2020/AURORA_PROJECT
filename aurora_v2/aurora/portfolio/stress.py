"""Stress and Monte Carlo: what the risk limits do under conditions we did not live.

Gemini's comparison flagged the absence of Monte Carlo and portfolio stress testing.
That criticism lands, and the reason it matters is specific: a single backtest is ONE
ordering of history. The same trades reordered can produce a very different drawdown,
and if the risk guard only survives one ordering it was never tested, it was lucky.

Three questions this module answers, all with pre-registered rules:
  1. reorder the returns - does the drawdown hold up? (iid and block bootstrap)
  2. make trading more expensive than measured - when does the edge disappear?
  3. force correlations to one, as they do in a crisis - how much does the book lose?

Nothing here predicts anything. It prices the tail so a limit can be set from
evidence instead of from the calmest month on record.
"""
import random
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Dict, List, Optional, Sequence

from aurora.stats import max_drawdown


@dataclass(frozen=True)
class StressResult:
    label: str
    mean_return_pct: float
    worst_dd_pct: float          # median across paths
    p95_dd_pct: float            # the bad-but-not-crazy outcome
    breach_rate: float           # share of paths breaching the drawdown limit
    paths: int

    def summary(self) -> str:
        return (f"{self.label}: worst-case drawdown median {self.worst_dd_pct:.1f}% "
                f"(p95 {self.p95_dd_pct:.1f}%), breach rate {self.breach_rate:.1%} "
                f"over {self.paths} paths")


def _drawdown_of(returns: Sequence[float]) -> float:
    curve, eq = [1.0], 1.0
    for r in returns:
        eq *= 1.0 + r
        curve.append(eq)
    return max_drawdown(curve)[1]


def bootstrap(returns: Sequence[float], paths: int = 1000, seed: int = 7,
              limit_pct: float = 40.0, label: str = "iid bootstrap") -> StressResult:
    """Resample returns with replacement: same trades, different order and luck."""
    if not returns:
        raise ValueError("no returns to resample")
    rng = random.Random(seed)   # seeded: a rerun must not change the verdict
    dds, means, breaches = [], [], 0
    for _ in range(paths):
        path = [rng.choice(returns) for _ in returns]
        dd = _drawdown_of(path)
        dds.append(dd)
        means.append(mean(path) * 12 * 100)
        if dd > limit_pct:
            breaches += 1
    dds.sort()
    return StressResult(label, mean(means), dds[len(dds) // 2],
                        dds[int(0.95 * (len(dds) - 1))], breaches / paths, paths)


def block_bootstrap(returns: Sequence[float], paths: int = 500, block: int = 6,
                    seed: int = 11, limit_pct: float = 40.0,
                    label: str = "block bootstrap") -> StressResult:
    """Resample contiguous blocks, keeping whatever autocorrelation exists.

    Plain iid resampling destroys momentum and volatility clustering, which makes a
    trend strategy look safer than it is. Blocks put those stretches back.
    """
    if not returns:
        raise ValueError("no returns to resample")
    n = len(returns)
    block = max(1, min(block, n))
    rng = random.Random(seed)
    dds, means, breaches = [], [], 0
    for _ in range(paths):
        path: List[float] = []
        while len(path) < n:
            start = rng.randrange(0, max(1, n - block + 1))
            path.extend(returns[start:start + block])
        path = path[:n]
        dd = _drawdown_of(path)
        dds.append(dd)
        means.append(mean(path) * 12 * 100)
        if dd > limit_pct:
            breaches += 1
    dds.sort()
    return StressResult(label, mean(means), dds[len(dds) // 2],
                        dds[int(0.95 * (len(dds) - 1))], breaches / paths, paths)


def cost_shock(returns: Sequence[float], extra_per_period: float,
               label: Optional[str] = None) -> Dict[str, float]:
    """Subtract extra cost each period until the edge dies.

    Returns the sharpest surviving cost per period, in basis points, and whether the
    strategy still has a positive mean after it. A strategy that cannot pay 3x
    measured cost is not robust, it is calibrated to one broker's table.
    """
    if not returns:
        raise ValueError("no returns")
    out = {}
    for mult in (1, 2, 3, 5, 8):
        adj = [r - extra_per_period * mult for r in returns]
        out[f"{mult}x"] = {"mean_pct": mean(adj) * 12 * 100,
                           "dd_pct": _drawdown_of(adj),
                           "sharpe": (mean(adj) / pstdev(adj) * (12 ** 0.5))
                           if len(adj) > 2 and pstdev(adj) > 0 else 0.0}
    if label:
        out["label"] = label
    return out


def correlated_shock(weights: Dict[str, float], asset_shocks: Dict[str, float],
                     crisis_correlation: float = 1.0) -> float:
    """Portfolio loss when every position falls together.

    In a crisis correlations go to one, so this deliberately ignores the diversification
    the calm-period matrix reports. `crisis_correlation` blends the two: 1.0 is the
    honest worst case, 0.0 pretends diversification survives a panic.
    """
    if not weights:
        return 0.0
    total = 0.0
    for sym, w in weights.items():
        shock = asset_shocks.get(sym, -0.20)      # unknown exposure gets a real loss
        total += w * shock * crisis_correlation
    return total


def liquidation_days(position_value: float, adv_value: float,
                     participation_cap: float = 0.10) -> float:
    """How many sessions it takes to leave a position without moving the market."""
    if position_value <= 0:
        return 0.0
    if adv_value <= 0:
        return float("inf")                    # unknown liquidity is not liquidity
    per_day = adv_value * participation_cap
    return position_value / per_day
