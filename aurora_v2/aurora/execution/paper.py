"""Paper broker: fills with spread, commission and slippage, and refuses to invent prices.

Two details that decide whether a backtest is honest:
  * entry pays half the spread (long lifts the ask, short hits the bid)
  * stop fills get adverse slippage; target fills do not (a limit is a limit)
  * a gap through the level fills at the open, not at the level
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..core.types import Side
from .costs import SwapTable, swap_cost


@dataclass(frozen=True)
class Fill:
    price: float
    commission: float
    slipped: float = 0.0


@dataclass
class PaperBroker:
    balance: float = 10_000.0
    spread: float = 0.00002          # full spread in price units (EURUSD 0.2 pip)
    commission_per_unit: float = 0.0
    swap: Optional["SwapTable"] = None
    slippage: float = 0.00001        # adverse slip applied to stop fills
    fills: List[Fill] = field(default_factory=list)

    def _commission(self, units: float) -> float:
        return abs(units) * self.commission_per_unit

    def charge_swap(self, symbol: str, side: Side, units: float, price: float,
                    days: float) -> float:
        """Accrue carry for `days` and take it out of the balance.

        Returns 0 when no calibrated table is attached: a guessed swap rate would
        silently re-price every backtest, so silence is the only safe default.
        """
        if self.swap is None or not self.swap.calibrated or days <= 0:
            return 0.0
        rate = self.swap.rate(symbol)
        if rate is None:
            return 0.0
        cost = swap_cost(abs(units) * price, rate.for_side(side), days)
        self.balance -= cost
        return cost

    def fill_entry(self, side: Side, units: float, price: float) -> Fill:
        if units <= 0:
            raise ValueError(f"units must be > 0, got {units}")
        px = price + self.spread / 2 if side is Side.LONG else price - self.spread / 2
        fill = Fill(price=px, commission=self._commission(units))
        self.fills.append(fill)
        self.balance -= fill.commission
        return fill

    def fill_exit(self, side: Side, units: float, price: float, *, stop_like: bool = False) -> Fill:
        if units <= 0:
            raise ValueError(f"units must be > 0, got {units}")
        px = price - self.spread / 2 if side is Side.LONG else price + self.spread / 2
        slipped = 0.0
        if stop_like:
            slipped = self.slippage
            px = px - slipped if side is Side.LONG else px + slipped
        fill = Fill(price=px, commission=self._commission(units), slipped=slipped)
        self.fills.append(fill)
        self.balance -= fill.commission
        return fill
