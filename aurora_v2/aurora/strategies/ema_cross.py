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
        if fast < 2 or slow < 3:
            raise ValueError("fast must be >= 2 and slow >= 3")
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

    # ---- fast path: one pass over the series ------------------------------
    def prepare(self, candles: Sequence[Candle]) -> List[Optional[Signal]]:
        n = len(candles)
        out: List[Optional[Signal]] = [None] * n
        if n < self.warmup():
            return out
        closes = [c.close for c in candles]
        f, s = ema(closes, self.fast), ema(closes, self.slow)
        look = self.stop_lookback

        for i in range(self.warmup(), n):
            if None in (f[i], s[i], f[i - 1], s[i - 1]):
                continue
            crossed_up = f[i - 1] <= s[i - 1] and f[i] > s[i]
            crossed_down = f[i - 1] >= s[i - 1] and f[i] < s[i]
            if not (crossed_up or crossed_down):
                continue

            last = candles[i]
            window = candles[i - look:i]
            if crossed_up:
                stop = min(c.low for c in window)
                if stop >= last.close:
                    continue
                target = last.close + self.rr * (last.close - stop)
                reason = (
                    f"EMA{self.fast} crossed above EMA{self.slow} at {last.close:.5f}; "
                    f"stop under {look}-bar low {stop:.5f}; target {self.rr:g}R"
                )
                out[i] = Signal(Side.LONG, last.close, stop, target, reason)
            else:
                stop = max(c.high for c in window)
                if stop <= last.close:
                    continue
                target = last.close - self.rr * (stop - last.close)
                reason = (
                    f"EMA{self.fast} crossed below EMA{self.slow} at {last.close:.5f}; "
                    f"stop over {look}-bar high {stop:.5f}; target {self.rr:g}R"
                )
                out[i] = Signal(Side.SHORT, last.close, stop, target, reason)
        return out

    def evaluate(self, candles: Sequence[Candle]) -> Optional[Signal]:
        """Single-shot view of the last bar (used by tests and ad hoc calls)."""
        if not candles:
            return None
        return self.prepare(candles)[-1]


STRATEGY_TYPES = {
    "ema_cross": EmaCross,
}
