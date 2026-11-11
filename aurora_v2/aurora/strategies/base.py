"""Strategy interface. A strategy is a pure function of closed candles.

It returns a Signal proposal or None. It never sizes a position, never places
anything, never touches the risk engine. That separation is the point.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Sequence

from ..core.types import Candle, Side


@dataclass(frozen=True)
class Signal:
    side: Side
    entry: float
    stop: float
    target: float
    reason: str


class Strategy(Protocol):
    name: str

    def warmup(self) -> int:
        """Number of candles needed before the first usable signal."""

    def evaluate(self, candles: Sequence[Candle]) -> Optional[Signal]:
        """Look at closed candles only; decide on the most recent close."""


def precompute(strategy: Strategy, candles: Sequence[Candle]) -> List[Optional[Signal]]:
    """Signals for every bar, in one pass where the strategy can do it.

    Without this the runner re-slices the series on every bar and the cost is
    quadratic: fine for a demo, useless for a parameter sweep on real data.
    A strategy may expose `prepare(candles)`; otherwise we fall back to
    evaluating each prefix, which is correct but slow.
    """
    prepare = getattr(strategy, "prepare", None)
    if callable(prepare):
        return list(prepare(candles))
    out: List[Optional[Signal]] = []
    for i in range(len(candles)):
        out.append(strategy.evaluate(candles[: i + 1]))
    return out
