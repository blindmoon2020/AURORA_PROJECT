"""Paper broker. Fills at the signal price plus a spread, charges commission,
and refuses to invent prices. Real brokers implement the same three methods.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..core.types import Side


@dataclass(frozen=True)
class Fill:
    price: float
    commission: float


@dataclass
class PaperBroker:
    balance: float = 10_000.0
    spread: float = 0.00002
    commission_per_unit: float = 0.0
    fills: List[Fill] = field(default_factory=list)

    def _commission(self, units: float) -> float:
        return abs(units) * self.commission_per_unit

    def fill_entry(self, side: Side, units: float, price: float) -> Fill:
        """Pay the spread on the way in: long lifts the ask, short hits the bid."""
        if units <= 0:
            raise ValueError(f"units must be > 0, got {units}")
        px = price + self.spread / 2 if side is Side.LONG else price - self.spread / 2
        fill = Fill(price=px, commission=self._commission(units))
        self.fills.append(fill)
        self.balance -= fill.commission
        return fill

    def fill_exit(self, side: Side, units: float, price: float) -> Fill:
        """Closing a long sells the bid, closing a short buys the ask."""
        if units <= 0:
            raise ValueError(f"units must be > 0, got {units}")
        px = price - self.spread / 2 if side is Side.LONG else price + self.spread / 2
        fill = Fill(price=px, commission=self._commission(units))
        self.fills.append(fill)
        self.balance -= fill.commission
        return fill
