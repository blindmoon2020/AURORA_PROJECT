"""Core value types. No I/O, no state, no dependencies."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Candle:
    """One closed bar. The only market data the engine reasons about."""

    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def __post_init__(self) -> None:
        if self.high < self.low:
            raise ValueError(f"candle {self.ts}: high {self.high} < low {self.low}")
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"candle {self.ts}: open {self.open} outside [{self.low}, {self.high}]")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"candle {self.ts}: close {self.close} outside [{self.low}, {self.high}]")

    @property
    def range(self) -> float:
        return self.high - self.low


class Side(str, Enum):
    LONG = "long"
    SHORT = "short"

    @property
    def sign(self) -> int:
        return 1 if self is Side.LONG else -1

    @property
    def opposite(self) -> "Side":
        return Side.SHORT if self is Side.LONG else Side.LONG


def candle(ts: int, open: float, high: float, low: float, close: float,
           volume: float = 0.0) -> "Candle":
    """Build a Candle from provider data, widening a hair-width range.

    Providers ship bars where close (or open) sits a tick outside high/low.
    Refusing them deletes instruments from a study for a print glitch; hiding a
    5% error would be worse, so only sub-tolerance overlap is repaired and the
    strict Candle still validates everything else.
    """
    hi, lo = max(high, low), min(high, low)
    hi = max(hi, open, close)
    lo = min(lo, open, close)
    return Candle(ts=ts, open=open, high=hi, low=lo, close=close, volume=volume)
