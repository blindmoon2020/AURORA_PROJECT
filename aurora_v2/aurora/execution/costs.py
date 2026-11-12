"""Holding costs: swap, financing and the Wednesday triple.

A position held for days is not free. An institutional desk prices carry before
it prices a signal, because carry is the one cost that cannot be traded away.

Honesty rule: the shipped table is EMPTY on purpose. Nobody knows your broker's
swap rates until you read them off the account. A guessed rate would quietly
change every backtest, so `SwapTable.calibrated` must be True before the runner
charges anything, and only `from_pairs` (real quotes) sets it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, Optional, Tuple

from ..core.types import Side

SECONDS_PER_YEAR = 365.0 * 86400.0


@dataclass(frozen=True)
class SwapRate:
    """Annual carry as a COST, per side. Positive = you pay, negative = you receive.

    Broker statements show a debit as a negative number; flip the sign when you
    build the table, so this code has one convention and no surprises.
    """

    long_annual_pct: float
    short_annual_pct: float

    def for_side(self, side: Side) -> float:
        return self.long_annual_pct if side is Side.LONG else self.short_annual_pct


@dataclass
class SwapTable:
    rates: Dict[str, SwapRate] = field(default_factory=dict)
    calibrated: bool = False
    source: str = ""
    default_rate: Optional[SwapRate] = None

    @classmethod
    def from_pairs(cls, pairs: Iterable[Tuple[str, float, float]], source: str = "") -> "SwapTable":
        """Build from (symbol, long_pct, short_pct) triples read off a real account."""
        table: Dict[str, SwapRate] = {}
        for symbol, long_pct, short_pct in pairs:
            table[symbol.upper()] = SwapRate(float(long_pct), float(short_pct))
        return cls(rates=table, calibrated=True, source=source)

    def rate(self, symbol: str) -> Optional[SwapRate]:
        return self.rates.get(symbol.upper(), self.default_rate)


def is_triple_swap_day(ts: int, triple_weekday: int = 2) -> bool:
    """True when the rollover at `ts` carries three days of swap instead of one.

    Wednesday is the common convention (value date jumps Friday->Monday). Some
    brokers charge it on Friday instead, so the weekday is a parameter, not a
    constant.
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc).weekday() == triple_weekday


def swap_cost(notional: float, annual_pct: float, days: float) -> float:
    """Carry charge for holding `days` at `annual_pct` (positive = you pay)."""
    return notional * (annual_pct / 100.0) * (days / 365.0)
