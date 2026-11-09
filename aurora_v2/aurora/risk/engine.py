"""Risk engine: the only place allowed to say no.

Rules, in the order they are checked:
  1. kill switch        - nothing trades until a human resets it
  2. valid geometry     - a stop that is not on the losing side is not a stop
  3. daily loss cap     - stop trading for the day once the cap is hit
  4. position count     - never more than N open at once
  5. one per symbol     - no stacking a symbol
  6. exposure ceiling   - notional may not exceed equity * max_leverage
  7. size > 0           - a trade too small to size is not taken

Position size always comes from account risk: units = (equity * risk%) / stop distance.
Every decision returns a human-readable reason, accepted or rejected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from ..core.types import Side


@dataclass(frozen=True)
class RiskLimits:
    risk_per_trade_pct: float = 0.5
    daily_loss_cap_pct: float = 2.0
    max_open_positions: int = 2
    max_leverage: float = 30.0

    def validate(self) -> None:
        if not 0 < self.risk_per_trade_pct <= 5:
            raise ValueError(f"risk_per_trade_pct must be in (0, 5], got {self.risk_per_trade_pct}")
        if not 0 < self.daily_loss_cap_pct <= 20:
            raise ValueError(f"daily_loss_cap_pct must be in (0, 20], got {self.daily_loss_cap_pct}")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be >= 1")
        if self.max_leverage <= 0:
            raise ValueError("max_leverage must be > 0")


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    units: float
    risk_money: float
    reason: str


@dataclass
class RiskEngine:
    limits: RiskLimits
    kill_switch: Optional[str] = None
    day_start_equity: Optional[float] = None
    realized_today: float = 0.0
    open_notional: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.limits.validate()

    # ---- day / state bookkeeping -------------------------------------------
    def start_day(self, equity: float) -> None:
        self.day_start_equity = equity
        self.realized_today = 0.0

    @property
    def daily_loss_pct(self) -> float:
        if not self.day_start_equity:
            return 0.0
        loss = -min(self.realized_today, 0.0)
        return loss / self.day_start_equity * 100.0

    def daily_cap_hit(self) -> bool:
        return self.daily_loss_pct >= self.limits.daily_loss_cap_pct

    def trip(self, reason: str) -> None:
        self.kill_switch = reason

    def reset(self) -> None:
        self.kill_switch = None

    def register_open(self, symbol: str, notional: float) -> None:
        self.open_notional[symbol] = self.open_notional.get(symbol, 0.0) + abs(notional)

    def register_close(self, symbol: str, pnl: float) -> None:
        self.open_notional.pop(symbol, None)
        self.realized_today += pnl

    def new_session(self, equity: float, is_new_day: bool) -> None:
        """Roll the day when the bar date changes."""
        if is_new_day or self.day_start_equity is None:
            self.start_day(equity)

    # ---- the decision ------------------------------------------------------
    def size_units(self, equity: float, entry: float, stop: float) -> tuple[float, float]:
        """Return (units, risk_money). Units 0.0 when geometry is unusable."""
        distance = abs(entry - stop)
        if distance <= 0:
            return 0.0, 0.0
        risk_money = equity * self.limits.risk_per_trade_pct / 100.0
        units = risk_money / distance
        return round(units, 6), round(risk_money, 2)

    def evaluate(
        self,
        *,
        symbol: str,
        side: Side,
        entry: float,
        stop: float,
        equity: float,
        ts: int = 0,
    ) -> RiskDecision:
        if self.kill_switch:
            return RiskDecision(False, 0.0, 0.0, f"kill switch active: {self.kill_switch}")

        # A long needs its stop below entry, a short above it.
        geometry_ok = stop < entry if side is Side.LONG else stop > entry
        if not geometry_ok:
            return RiskDecision(
                False, 0.0, 0.0,
                f"invalid stop: {side.value} entry {entry} stop {stop} is on the wrong side",
            )

        if self.daily_cap_hit():
            return RiskDecision(
                False, 0.0, 0.0,
                f"daily loss cap hit: {self.daily_loss_pct:.2f}% >= "
                f"{self.limits.daily_loss_cap_pct:.2f}% (realized {self.realized_today:.2f})",
            )

        if len(self.open_notional) >= self.limits.max_open_positions:
            return RiskDecision(
                False, 0.0, 0.0,
                f"max open positions reached: {len(self.open_notional)}/"
                f"{self.limits.max_open_positions}",
            )

        if symbol in self.open_notional:
            return RiskDecision(False, 0.0, 0.0, f"already positioned in {symbol}")

        units, risk_money = self.size_units(equity, entry, stop)
        if units <= 0:
            return RiskDecision(
                False, 0.0, 0.0,
                f"sized to zero: equity {equity:.2f} risk {self.limits.risk_per_trade_pct}% "
                f"over stop distance {abs(entry - stop):.6f}",
            )

        notional = units * entry
        ceiling = equity * self.limits.max_leverage
        if notional > ceiling:
            return RiskDecision(
                False, 0.0, 0.0,
                f"exposure ceiling: notional {notional:,.2f} > equity*{self.limits.max_leverage:g} "
                f"= {ceiling:,.2f} (stop distance {abs(entry - stop):.6f} too tight)",
            )

        return RiskDecision(
            True,
            units,
            risk_money,
            f"risk {risk_money:,.2f} = {self.limits.risk_per_trade_pct}% of equity "
            f"{equity:,.2f}; stop distance {abs(entry - stop):.6f}; units {units:g}; "
            f"notional {notional:,.2f}",
        )
