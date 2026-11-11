"""Metrics that can be defended. Unknown numbers are not printed.

Two curves are kept, because they answer different questions:
  * realized equity - what the account actually held, no optimism
  * mark-to-market  - realized plus open position, the curve a client would see
Drawdown and Sharpe are reported off the mark-to-market curve.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .. import stats


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
    bars_held: int = 0
    risk_money: float = 0.0
    decision_id: str = ""


@dataclass
class Metrics:
    starting_balance: float
    periods_per_year: int = 252
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)      # realized
    mtm_curve: List[float] = field(default_factory=list)         # realized + open
    bar_returns: List[float] = field(default_factory=list)
    signals: int = 0
    approved: int = 0
    rejected: int = 0

    # ---- trade statistics --------------------------------------------------
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
    def avg_bars_held(self) -> float:
        return sum(t.bars_held for t in self.trades) / self.count if self.count else 0.0

    @property
    def exit_mix(self) -> dict:
        out: dict = {}
        for t in self.trades:
            out[t.exit_reason] = out.get(t.exit_reason, 0) + 1
        return out

    # ---- curve statistics --------------------------------------------------
    @property
    def max_drawdown_pct(self) -> float:
        return stats.max_drawdown(self.mtm_curve or self.equity_curve)[1]

    @property
    def realized_drawdown_pct(self) -> float:
        return stats.max_drawdown(self.equity_curve)[1]

    @property
    def sharpe(self) -> float:
        return stats.sharpe(self.bar_returns, self.periods_per_year)

    @property
    def sortino(self) -> float:
        return stats.sortino(self.bar_returns, self.periods_per_year)

    @property
    def calmar(self) -> float:
        return stats.calmar(self.mtm_curve or self.equity_curve, self.periods_per_year)

    @property
    def t_stat(self) -> float:
        return stats.t_stat(self.bar_returns)

    @property
    def p_value(self) -> float:
        n = len(self.bar_returns)
        return stats.t_p_value(self.t_stat, n - 1) if n > 2 else 1.0

    @property
    def psr(self) -> float:
        return stats.probabilistic_sharpe_ratio(self.bar_returns)

    @property
    def mean_bar_return_pct(self) -> float:
        return stats.mean(self.bar_returns) * 100

    def ci_expectancy(self, confidence: float = 0.95) -> tuple[float, float]:
        return stats.confidence_interval(self.bar_returns, confidence)

    def report(self) -> str:
        pf = "n/a" if self.profit_factor is None else f"{self.profit_factor:.2f}"
        lo, hi = self.ci_expectancy()
        return "\n".join([
            f"data bars={len(self.mtm_curve)} periods/yr={self.periods_per_year}",
            f"signals={self.signals} approved={self.approved} rejected={self.rejected}",
            f"trades={self.count} wins={self.wins} losses={self.losses} "
            f"win_rate={self.win_rate:.1f}% avg_hold={self.avg_bars_held:.0f} bars",
            f"profit_factor={pf} expectancy={self.expectancy:,.2f} avg_R={self.avg_r:.2f}R",
            f"net_pnl={self.net_pnl:,.2f} start={self.starting_balance:,.2f} "
            f"final={self.final_equity:,.2f}",
            f"sharpe={self.sharpe:.2f} sortino={self.sortino:.2f} calmar={self.calmar:.2f}",
            f"maxDD_mtm={self.max_drawdown_pct:.2f}% maxDD_realized={self.realized_drawdown_pct:.2f}%",
            f"t_stat={self.t_stat:.2f} p_value={self.p_value:.3f} psr={self.psr:.3f}",
            f"mean_bar_return={self.mean_bar_return_pct:.4f}% "
            f"95%CI=[{lo*100:.4f}%,{hi*100:.4f}%]",
            f"exits={self.exit_mix}",
        ])


def periods_per_year_for(bar_seconds: int) -> int:
    """FX convention: 252 trading days a year, 24 hours a day."""
    if bar_seconds <= 0:
        return 252
    bars_per_day = max(1, round(86_400 / bar_seconds))
    return int(252 * bars_per_day)
