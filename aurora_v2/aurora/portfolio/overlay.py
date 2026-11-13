"""Overlays that cut risk without pretending to predict: volatility targeting and a trend brake.

Both read only the past. A risk overlay that uses today's realised volatility to
decide yesterday's position is a backtest artefact, so every scaler here is built
from the window that ends before the return it scales.
"""
from statistics import stdev
from typing import List, Sequence

import math


def vol_target(returns: Sequence[float], target: float = 0.12, window: int = 6,
               cap: float = 1.0, periods_per_year: int = 12) -> List[float]:
    """Scale each return by target/realised volatility of the preceding window."""
    if window < 2:
        raise ValueError("window must be at least 2")
    out: List[float] = []
    for i, r in enumerate(returns):
        history = list(returns[max(0, i - window):i])
        if len(history) < 2:
            out.append(0.0)                    # no history, no position
            continue
        vol = stdev(history) * math.sqrt(periods_per_year)
        if vol < 1e-9:
            out.append(0.0)
            continue
        out.append(r * min(cap, target / vol))
    return out


def trend_brake(returns: Sequence[float], benchmark: Sequence[float],
                window: int = 10) -> List[float]:
    """Stand aside while the benchmark is below where it was `window` periods ago.

    The classic monthly rule, applied strictly to information available before the
    return being scaled.
    """
    if len(returns) != len(benchmark):
        raise ValueError("returns and benchmark must line up")
    level, out = 1.0, []
    levels = [level]
    for b in benchmark:
        level *= 1.0 + b
        levels.append(level)
    for i, r in enumerate(returns):
        past = levels[i - window] if i - window >= 0 else None
        if past is None or past <= 0:
            out.append(r)                      # not enough history to judge
            continue
        out.append(r if levels[i] >= past else 0.0)
    return out
