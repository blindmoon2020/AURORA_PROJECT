"""Risk allocation: the part of the platform that earns its keep without an edge.

The global study showed the momentum rule loses to holding SPY on return (0.08 vs
0.53) but had less than half the drawdown (13.6% vs 34%). That is a real, useful
property, and it is what this module turns into a portfolio: hold a basket, size
each holding by its own risk, and require a trend to be positive before paying for
the risk.

Nothing here forecasts a return. It controls how much of the portfolio one asset
may hurt, which is a decision that can be defended without a prediction.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.types import Candle


@dataclass
class AllocationResult:
    returns: List[float]
    sharpe: float
    max_dd_pct: float
    total_return_pct: float
    avg_positions: float
    rebalances: int


def align(series: Dict[str, Sequence[Candle]]) -> Tuple[List[int], Dict[str, Dict[int, float]]]:
    """Daily returns per asset keyed by timestamp, on the union of dates."""
    out: Dict[str, Dict[int, float]] = {}
    grid = set()
    for sym, candles in series.items():
        row: Dict[int, float] = {}
        for i in range(1, len(candles)):
            prev, cur = candles[i - 1].close, candles[i].close
            if prev > 0:
                row[candles[i].ts] = cur / prev - 1.0
        out[sym] = row
        grid.update(row)
    return sorted(grid), out


def inverse_vol_weights(
    returns: Dict[str, float], cap: float = 0.25
) -> Dict[str, float]:
    """Water-filling inverse-vol weights: cap each name, then refill the rest.

    With fewer names than 1/cap the cap cannot be met and the book is simply
    under-invested. That is reported by the sum being below one, never hidden by
    silently raising the cap.
    """
    inv = {k: (1.0 / v if v > 1e-9 else 0.0) for k, v in returns.items()}
    inverse = {k: v for k, v in inv.items() if v > 0}
    if not inverse:
        return {}
    out: Dict[str, float] = {}
    remaining = 1.0
    live = dict(inverse)
    while live and remaining > 1e-12:
        total = sum(live.values())
        provisional = {k: v / total * remaining for k, v in live.items()}
        over = {k: p for k, p in provisional.items() if p > cap + 1e-12}
        if not over:
            out.update(provisional)
            remaining = 0.0
            break
        for k in over:
            out[k] = cap
            remaining -= cap
            del live[k]
    if len(out) == 1 and cap >= 1.0:
        out = {k: 1.0 for k in out}
    return out


def run_allocation(
    series: Dict[str, Sequence[Candle]],
    vol_window: int = 60,
    rebalance: int = 21,
    target_vol: float = 0.10,
    cap: float = 0.25,
    trend_filter: bool = True,
    trend_lookback: int = 252,
    cost_rate: float = 0.0003,
    benchmark: Optional[str] = None,
) -> AllocationResult:
    """Monthly inverse-vol allocation with an optional trend gate."""
    grid, rets = align(series)
    closes = {s: {c.ts: c.close for c in candles} for s, candles in series.items()}
    weights: Dict[str, float] = {}
    out: List[float] = []
    rebalances = 0
    active_counts: List[int] = []

    for i, ts in enumerate(grid):
        if i % rebalance == 0 and i >= vol_window + trend_lookback:
            hist = {s: [rets[s][t] for t in grid[max(0, i - vol_window):i] if t in rets[s]]
                    for s in series}
            vols = {s: (stdev(h) * (252 ** 0.5)) for s, h in hist.items() if len(h) >= 20}
            if trend_filter:
                eligible = {}
                for s, v in vols.items():
                    past = [t for t in grid[max(0, i - trend_lookback):i] if t in closes[s]]
                    if len(past) >= 100 and closes[s][past[-1]] > closes[s][past[0]]:
                        eligible[s] = v
                vols = eligible
            new_w = inverse_vol_weights(vols, cap=cap)
            # scale the whole book so its own realised vol matches the target
            book_vol = 0.0
            if new_w:
                cov = []
                for t in grid[max(0, i - vol_window):i]:
                    r = sum(new_w[s] * rets[s].get(t, 0.0) for s in new_w)
                    cov.append(r)
                book_vol = stdev(cov) * (252 ** 0.5) if len(cov) > 2 else 0.0
            scale = min(2.0, target_vol / book_vol) if book_vol > 1e-9 else 0.0
            turnover = sum(abs(scale * new_w.get(s, 0.0) - weights.get(s, 0.0)) for s in set(new_w) | set(weights))
            weights = {s: scale * w for s, w in new_w.items()}
            out.append(-turnover * cost_rate)
            rebalances += 1
            active_counts.append(len(weights))
            continue
        day = sum(weights.get(s, 0.0) * rets[s].get(ts, 0.0) for s in weights)
        out.append(day)

    if not out:
        return AllocationResult([], 0.0, 0.0, 0.0, 0.0, 0)
    from ..stats import max_drawdown, sharpe
    curve, eq = [1.0], 1.0
    for r in out:
        eq *= 1 + r
        curve.append(eq)
    return AllocationResult(
        returns=out,
        sharpe=sharpe(out, 252),
        max_dd_pct=max_drawdown(curve)[1],
        total_return_pct=(curve[-1] - 1.0) * 100.0,
        avg_positions=(mean(active_counts) if active_counts else 0.0),
        rebalances=rebalances,
    )
