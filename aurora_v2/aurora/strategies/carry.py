"""H1 · FX carry: hold the higher-yielding currency, funded by the lower one.

The premise is the forward premium puzzle, not a chart shape. Everything that
decides the result is explicit: which rate, how stale it may be, and how often
the ranking is allowed to change.
"""
from __future__ import annotations

from bisect import bisect_right
from typing import Dict, List, Sequence

from ..core.types import Candle


def rate_at(ts: int, series: Dict[int, float]) -> float | None:
    """The rate that was published and known at `ts`, never a future one."""
    keys = sorted(series)
    i = bisect_right(keys, ts) - 1
    return series[keys[i]] if i >= 0 else None


def carry_positions(
    candles: Sequence[Candle],
    base_rates: Dict[int, float],
    quote_rates: Dict[int, float],
    rebalance_days: int = 21,
) -> List[float]:
    if rebalance_days < 1:
        raise ValueError("rebalance_days must be positive")
    positions: List[float] = []
    current = 0.0
    for i, c in enumerate(candles):
        if i % rebalance_days == 0:
            b = rate_at(c.ts, base_rates)
            q = rate_at(c.ts, quote_rates)
            if b is None or q is None:
                current = 0.0            # no rate published yet: stand aside, do not guess
            elif b > q:
                current = 1.0            # long the pair: buy the high yielder
            elif b < q:
                current = -1.0
            else:
                current = 0.0
        positions.append(current)
    return positions
