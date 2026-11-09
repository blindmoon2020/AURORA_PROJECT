"""Metrics that can be defended. If a number here is unknown, it is not printed."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Trade:
    symbol: str
    side: str
    entry: float
    exit: float
    units: float
    pnl: float
    r_multiple: float
    opened_ts: int
    closed_ts: int
    exit_reason: str
    strategy: str = ""


@dataclass
class Metrics:
    starting_balance: float
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    signals: int = 0
    approved: int = 0
    rejected: int = 0

    @property
    def count(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.pnl > 0)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.trades if t.pnl <= 0)

    @property
    def win_rate(self) -> float:
        return self.wins / self.count * 100 if self.count else 0.0

    @property
    def gross_profit(self) -> float:
        return sum(t.pnl for t in self.trades if t.pnl > 0)

    @property
    def gross_loss(self) -> float:
        return sum(t.pnl for t in self.trades if t.pnl <= 0)

    @property
    def profit_factor(self) -> Optional[float]:
        if not self.gross_loss:
            return None if not self.gross_profit else float("inf")
        return self.gross_profit / abs(self.gross_loss)

    @property
    def net_pnl(self) -> float:
        return sum(t.pnl for t in self.trades)

    @property
    def final_equity(self) -> float:
        return self.equity_curve[-1] if self.equity_curve else self.starting_balance

    @property
    def expectancy(self) -> float:
        return self.net_pnl / self.count if self.count else 0.0

    @property
    def avg_r(self) -> float:
        return sum(t.r_multiple for t in self.trades) / self.count if self.count else 0.0

    @property
    def max_drawdown_pct(self) -> float:
        peak, worst = float("-inf"), 0.0
        for eq in self.equity_curve:
            peak = max(peak, eq)
            if peak > 0:
                worst = max(worst, (peak - eq) / peak * 100)
        return worst

    def report(self) -> str:
        pf = "n/a" if self.profit_factor is None else f"{self.profit_factor:.2f}"
        lines = [
            f"signals={self.signals} approved={self.approved} rejected={self.rejected}",
            f"trades={self.count} wins={self.wins} losses={self.losses} "
            f"win_rate={self.win_rate:.1f}%",
            f"profit_factor={pf} expectancy={self.expectancy:,.2f} avg_R={self.avg_r:.2f}R",
            f"max_drawdown={self.max_drawdown_pct:.2f}% net_pnl={self.net_pnl:,.2f}",
            f"start={self.starting_balance:,.2f} final={self.final_equity:,.2f}",
        ]
        return "\n".join(lines)
