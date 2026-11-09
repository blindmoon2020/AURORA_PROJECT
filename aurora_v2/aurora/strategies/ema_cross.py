"""EMA cross with a swing stop and a fixed reward multiple.

Baseline strategy, deliberately simple: it exists to prove the plumbing,
not to make money. Numbers live in the DNA file, not here.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from ..core.types import Candle, Side
from .base import Signal


def ema(values: Sequence[float], period: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(values)
    if period <= 0 or len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


class EmaCross:
    def __init__(
        self,
        name: str = "ema_cross",
        fast: int = 20,
        slow: int = 50,
        stop_lookback: int = 10,
        rr: float = 2.0,
    ) -> None:
        if fast >= slow:
            raise ValueError(f"fast ({fast}) must be < slow ({slow})")
        if stop_lookback < 1:
            raise ValueError("stop_lookback must be >= 1")
        if rr <= 0:
            raise ValueError("rr must be > 0")
        self.name = name
        self.fast = int(fast)
        self.slow = int(slow)
        self.stop_lookback = int(stop_lookback)
        self.rr = float(rr)

    def warmup(self) -> int:
        return self.slow + self.stop_lookback + 1

    def evaluate(self, candles: Sequence[Candle]) -> Optional[Signal]:
        if len(candles) < self.warmup():
            return None
        closes = [c.close for c in candles]
        f, s = ema(closes, self.fast), ema(closes, self.slow)
        i = len(candles) - 1
        if None in (f[i], s[i], f[i - 1], s[i - 1]):
            return None

        crossed_up = f[i - 1] <= s[i - 1] and f[i] > s[i]
        crossed_down = f[i - 1] >= s[i - 1] and f[i] < s[i]
        if not (crossed_up or crossed_down):
            return None

        last = candles[i]
        window = candles[i - self.stop_lookback:i]
        if crossed_up:
            stop = min(c.low for c in window)
            if stop >= last.close:
                return None
            target = last.close + self.rr * (last.close - stop)
            reason = (
                f"EMA{self.fast} crossed above EMA{self.slow} at {last.close:.5f}; "
                f"stop under {self.stop_lookback}-bar low {stop:.5f}; target {self.rr:g}R"
            )
            return Signal(Side.LONG, last.close, stop, target, reason)

        stop = max(c.high for c in window)
        if stop <= last.close:
            return None
        target = last.close - self.rr * (stop - last.close)
        reason = (
            f"EMA{self.fast} crossed below EMA{self.slow} at {last.close:.5f}; "
            f"stop over {self.stop_lookback}-bar high {stop:.5f}; target {self.rr:g}R"
        )
        return Signal(Side.SHORT, last.close, stop, target, reason)


STRATEGY_TYPES = {
    "ema_cross": EmaCross,
}
