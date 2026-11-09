"""Strategy interface. A strategy is a pure function of closed candles.

It returns a Signal proposal or None. It never sizes a position, never places
anything, and never touches the risk engine. That separation is the point.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, Sequence

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
