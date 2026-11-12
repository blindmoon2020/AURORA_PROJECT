"""Time-series momentum (H2), implemented the way the literature tests it.

The premise: an instrument's own past 12-month return has predictive power for
the next month, across asset classes, and the effect survives costs because
turnover is low (monthly).

Implementation choices that decide whether the number is real:
  * signal computed on closes up to and including bar t, position applied to the
    return from t+1 onward - no same-bar information
  * rebalance monthly, not daily: momentum is a slow signal and daily rebalancing
    would multiply costs by ~21 for no added information
  * position size scaled inversely to realised volatility, capped, so one wild
    instrument cannot dominate the portfolio
  * a flip costs money: cost = turnover * cost_rate, charged on the bar it happens

The output is deliberately boring: an equity curve, the number of flips, and the
honest metrics computed by aurora.stats.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from ..core.types import Candle
from ..stats import max_drawdown, sharpe, sortino


@dataclass
class MomentumResult:
    symbol: str
    bars: int
    flips: int
    total_return_pct: float
    sharpe: float
    sortino: float
    max_dd_pct: float
    hit_rate_pct: float
    avg_abs_exposure: float
    daily_returns: List[float] = field(default_factory=list)


def _returns(closes: Sequence[float]) -> List[float]:
    out: List[float] = [0.0]
    for prev, cur in zip(closes, closes[1:]):
        out.append(cur / prev - 1.0 if prev else 0.0)
    return out


def _realised_vol(returns: Sequence[float], window: int, index: int) -> float:
    start = max(1, index - window + 1)
    sample = [r for r in returns[start:index + 1] if r is not None]
    if len(sample) < 20:
        return 0.0
    mean = sum(sample) / len(sample)
    var = sum((r - mean) ** 2 for r in sample) / (len(sample) - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def backtest_tsmom(
    candles: Sequence[Candle],
    symbol: str = "",
    lookback: int = 252,
    vol_window: int = 60,
    vol_target: float = 0.10,
    max_leverage: float = 3.0,
    cost_rate: float = 0.0008,
    rebalance_days: int = 21,
) -> MomentumResult:
    """Long/short time-series momentum with volatility targeting and costs."""
    closes = [c.close for c in candles]
    if len(closes) < lookback + 30:
        raise ValueError(f"{symbol}: {len(closes)} bars is not enough for lookback {lookback}")

    rets = _returns(closes)
    equity = 1.0
    curve: List[float] = [equity]
    position = 0.0
    flips = 0
    hit = 0
    active = 0
    exposures: List[float] = []
    prev_month = None

    for i in range(lookback, len(closes) - 1):
        month = candles[i].ts // (86_400 * 21)  # crude monthly bucket, deterministic
        if month != prev_month:
            prev_month = month
            momentum = closes[i] / closes[i - lookback] - 1.0
            want = 1.0 if momentum > 0 else (-1.0 if momentum < 0 else 0.0)
            vol = _realised_vol(rets, vol_window, i)
            scale = min(max_leverage, vol_target / vol) if vol > 0 else 1.0
            target = want * scale
        else:
            target = position

        turnover = abs(target - position)
        if turnover > 0:
            flips += 1
            equity -= turnover * cost_rate
            position = target

        r = rets[i + 1]
        pnl = position * r
        if position != 0:
            active += 1
            if pnl > 0:
                hit += 1
        equity *= (1.0 + pnl)
        curve.append(equity)
        exposures.append(abs(position))

    daily = [curve[j] / curve[j - 1] - 1.0 for j in range(1, len(curve))]
    return MomentumResult(
        symbol=symbol or getattr(candles[0], "symbol", "") or "series",
        bars=len(daily),
        flips=flips,
        total_return_pct=(curve[-1] - 1.0) * 100.0,
        sharpe=sharpe(daily, 252),
        sortino=sortino(daily, 252),
        max_dd_pct=max_drawdown(curve)[1],
        hit_rate_pct=(100.0 * hit / active) if active else 0.0,
        avg_abs_exposure=(sum(exposures) / len(exposures)) if exposures else 0.0,
        daily_returns=daily,
    )


def combine(series: Dict[str, List[float]], weights: Optional[Dict[str, float]] = None) -> List[float]:
    """Equal-weight (default) combination of per-symbol daily return streams."""
    symbols = [s for s in series if series[s]]
    if not symbols:
        return []
    length = min(len(series[s]) for s in symbols)
    w = weights or {s: 1.0 / len(symbols) for s in symbols}
    out = []
    for i in range(length):
        out.append(sum(w[s] * series[s][len(series[s]) - length + i] for s in symbols))
    return out
