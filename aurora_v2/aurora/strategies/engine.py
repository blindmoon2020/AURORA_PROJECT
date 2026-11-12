"""Position-series engine: one honest way to turn a signal series into a return series.

Every hypothesis in V1 has to be measured the same way, or the comparison between
them means nothing. This is that way: cost charged on every change of position,
optional volatility targeting, and no stop-loss heroics that a rule never
specified.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from ..core.types import Candle
from ..stats import max_drawdown, sharpe, stdev


@dataclass
class PositionRun:
    returns: List[float]
    equity: List[float]
    flips: int          # any change of size, including a volatility rescale
    sign_flips: int     # direction changes only: the ones that carry a real cost
    sharpe: float
    max_dd_pct: float
    total_return_pct: float
    avg_abs_position: float
    exposure_days: int


def realized_vol(returns: Sequence[float], window: int) -> List[float]:
    out = []
    for i in range(len(returns)):
        start = max(0, i - window + 1)
        chunk = returns[start:i + 1]
        out.append(stdev(chunk) * (252 ** 0.5) if len(chunk) > 1 else 0.0)
    return out


def run_positions(
    candles: Sequence[Candle],
    positions: Sequence[float],
    cost_rate: float,
    vol_target: float | None = None,
    max_leverage: float = 3.0,
    vol_window: int = 60,
) -> PositionRun:
    if len(candles) != len(positions):
        raise ValueError("positions must line up with candles one for one")
    if len(candles) < 3:
        raise ValueError("need at least three bars")

    rets = [candles[i].close / candles[i - 1].close - 1.0 for i in range(1, len(candles))]
    # position decided on bar i-1 is what earns the return of bar i
    raw = [float(positions[i - 1]) for i in range(1, len(candles))]

    if vol_target is not None:
        vols = realized_vol(rets, vol_window)
        scaled = []
        for i, p in enumerate(raw):
            v = vols[i]
            scale = (vol_target / v) if v > 1e-9 else 0.0
            scaled.append(max(-max_leverage, min(max_leverage, p * scale)))
        raw = scaled

    out, flips, sign_flips, prev, prev_sign = [], 0, 0, 0.0, 0
    for i, p in enumerate(raw):
        turnover = abs(p - prev)
        if turnover > 1e-12:
            flips += 1
        sign = (1 if p > 0 else (-1 if p < 0 else 0))
        if sign != prev_sign:
            sign_flips += 1
            prev_sign = sign
        out.append(p * rets[i] - turnover * cost_rate)
        prev = p

    curve, eq = [1.0], 1.0
    for r in out:
        eq *= 1.0 + r
        curve.append(eq)
    return PositionRun(
        returns=out,
        equity=curve,
        flips=flips,
        sign_flips=sign_flips,
        sharpe=sharpe(out, 252),
        max_dd_pct=max_drawdown(curve)[1],
        total_return_pct=(curve[-1] - 1.0) * 100.0,
        avg_abs_position=sum(abs(p) for p in raw) / len(raw) if raw else 0.0,
        exposure_days=sum(1 for p in raw if abs(p) > 1e-12),
    )


def combine(return_streams: Sequence[Sequence[float]]) -> List[float]:
    """Equal weight across streams, aligned on the shortest common length, from the end."""
    if not return_streams:
        return []
    n = min(len(s) for s in return_streams)
    return [sum(s[len(s) - n + i] for s in return_streams) / len(return_streams) for i in range(n)]
