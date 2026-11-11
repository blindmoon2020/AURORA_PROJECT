"""Risk engine: the only place allowed to say no.

Checks, in order:
  1. kill switch          - nothing trades until a human resets it
  2. total drawdown cap   - the account survives, or trading stops, whichever first
  3. valid geometry       - a stop on the losing side is not a stop
  4. daily loss cap       - stop for the day once it is hit
  5. daily trade cap      - churn is a cost centre, not an edge
  6. position count       - never more than N open at once
  7. one per symbol       - no stacking
  8. exposure ceiling     - notional <= equity * max_leverage
  9. size > 0             - a trade too small to size is not taken

Size always comes from account risk: units = equity * risk% / stop distance.
Every decision returns a reason, accepted or rejected.
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
    max_daily_trades: int = 6
    max_total_drawdown_pct: float = 12.0

    def validate(self) -> None:
        if not 0 < self.risk_per_trade_pct <= 5:
            raise ValueError(f"risk_per_trade_pct must be in (0, 5], got {self.risk_per_trade_pct}")
        if not 0 < self.daily_loss_cap_pct <= 20:
            raise ValueError(f"daily_loss_cap_pct must be in (0, 20], got {self.daily_loss_cap_pct}")
        if self.max_open_positions < 1:
            raise ValueError("max_open_positions must be >= 1")
        if self.max_leverage <= 0:
            raise ValueError("max_leverage must be > 0")
        if self.max_daily_trades < 1:
            raise ValueError("max_daily_trades must be >= 1")
        if not 0 < self.max_total_drawdown_pct <= 50:
            raise ValueError("max_total_drawdown_pct must be in (0, 50]")


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
    peak_equity: Optional[float] = None
    realized_today: float = 0.0
    trades_today: int = 0
    open_notional: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.limits.validate()

    # ---- state -------------------------------------------------------------
    def start_day(self, equity: float) -> None:
        self.day_start_equity = equity
        self.realized_today = 0.0
        self.trades_today = 0

    def observe_equity(self, equity: float) -> None:
        """Track the high-water mark; trip the kill switch on a deep drawdown."""
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity
        if self.peak_equity and self.peak_equity > 0:
            dd = (self.peak_equity - equity) / self.peak_equity * 100.0
            if dd >= self.limits.max_total_drawdown_pct and not self.kill_switch:
                self.trip(f"total drawdown {dd:.2f}% >= {self.limits.max_total_drawdown_pct}%")

    @property
    def daily_loss_pct(self) -> float:
        if not self.day_start_equity:
            return 0.0
        return -min(self.realized_today, 0.0) / self.day_start_equity * 100.0

    def daily_cap_hit(self) -> bool:
        return self.daily_loss_pct >= self.limits.daily_loss_cap_pct

    def trip(self, reason: str) -> None:
        self.kill_switch = reason

    def reset(self) -> None:
        self.kill_switch = None
        self.peak_equity = None

    def register_open(self, symbol: str, notional: float) -> None:
        self.open_notional[symbol] = self.open_notional.get(symbol, 0.0) + abs(notional)
        self.trades_today += 1

    def register_close(self, symbol: str, pnl: float) -> None:
        self.open_notional.pop(symbol, None)
        self.realized_today += pnl

    # ---- sizing ------------------------------------------------------------
    def size_units(self, equity: float, entry: float, stop: float) -> tuple[float, float]:
        distance = abs(entry - stop)
        if distance <= 0:
            return 0.0, 0.0
        risk_money = equity * self.limits.risk_per_trade_pct / 100.0
        return round(risk_money / distance, 6), round(risk_money, 2)

    # ---- the decision ------------------------------------------------------
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

        if self.trades_today >= self.limits.max_daily_trades:
            return RiskDecision(
                False, 0.0, 0.0,
                f"daily trade cap hit: {self.trades_today}/{self.limits.max_daily_trades}",
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
                f"exposure ceiling: notional {notional:,.2f} > equity*{self.limits.max_leverage:g}"
                f" = {ceiling:,.2f} (stop distance {abs(entry - stop):.6f} too tight)",
            )

        return RiskDecision(
            True, units, risk_money,
            f"risk {risk_money:,.2f} = {self.limits.risk_per_trade_pct}% of equity "
            f"{equity:,.2f}; stop distance {abs(entry - stop):.6f}; units {units:g}; "
            f"notional {notional:,.2f}",
        )
