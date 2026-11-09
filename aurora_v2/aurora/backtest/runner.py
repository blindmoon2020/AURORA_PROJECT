"""The vertical slice: data -> strategy -> risk -> paper broker -> journal -> metrics.

Accounting is deliberate and testable:
  * equity is realized cash only; no mark-to-market fantasy
  * a position that touches stop and target in the same bar is closed at the STOP
  * commissions are charged on both legs and are included in trade pnl
  * final_equity == starting_balance + sum(trade.pnl)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

from ..core.events import (
    EventBus,
    ExitEvent,
    FillEvent,
    MarketEvent,
    OrderEvent,
    RiskDecisionEvent,
    SignalEvent,
)
from ..core.types import Candle, Side
from ..execution.paper import PaperBroker
from ..journal.decision_log import DecisionLog, DecisionRecord
from ..risk.engine import RiskEngine
from ..strategies.base import Signal, Strategy
from ..strategies.dna import StrategyDna
from .metrics import Metrics, Trade


@dataclass
class OpenPosition:
    symbol: str
    side: Side
    entry: float
    stop: float
    target: float
    units: float
    opened_ts: int
    strategy: str
    entry_commission: float


@dataclass
class BacktestRun:
    metrics: Metrics
    log: DecisionLog
    bus: EventBus
    trades: List[Trade] = field(default_factory=list)

    @property
    def rejected_reasons(self) -> List[str]:
        return [r.reason for r in self.log.rejected()]


def _exit_for(pos: OpenPosition, candle: Candle) -> Optional[tuple]:
    """Stop wins ties. Conservative on purpose."""
    if pos.side is Side.LONG:
        if candle.low <= pos.stop:
            return pos.stop, "stop"
        if candle.high >= pos.target:
            return pos.target, "target"
    else:
        if candle.high >= pos.stop:
            return pos.stop, "stop"
        if candle.low <= pos.target:
            return pos.target, "target"
    return None


def _close(
    pos: OpenPosition,
    broker: PaperBroker,
    exit_price: float,
    exit_reason: str,
    ts: int,
    risk: RiskEngine,
    bus: EventBus,
    trades: List[Trade],
) -> Trade:
    fill = broker.fill_exit(pos.side, pos.units, exit_price)
    gross = (fill.price - pos.entry) * pos.side.sign * pos.units
    broker.balance += gross - fill.commission
    pnl = gross - fill.commission - pos.entry_commission
    risk_amount = pos.units * abs(pos.entry - pos.stop)
    trade = Trade(
        symbol=pos.symbol,
        side=pos.side.value,
        entry=pos.entry,
        exit=fill.price,
        units=pos.units,
        pnl=pnl,
        r_multiple=pnl / risk_amount if risk_amount else 0.0,
        opened_ts=pos.opened_ts,
        closed_ts=ts,
        exit_reason=exit_reason,
        strategy=pos.strategy,
    )
    trades.append(trade)
    risk.register_close(pos.symbol, pnl)
    bus.publish(
        ExitEvent(ts=ts, symbol=pos.symbol, price=fill.price, pnl=pnl, exit_reason=exit_reason)
    )
    return trade


def run_backtest(
    candles: Sequence[Candle],
    dna: StrategyDna,
    strategy: Optional[Strategy] = None,
    starting_balance: float = 10_000.0,
    broker: Optional[PaperBroker] = None,
    log_path: Optional[str | Path] = None,
) -> BacktestRun:
    if not candles:
        raise ValueError("no candles to backtest")
    candles = list(candles)
    strat = strategy or dna.build()
    broker = broker or PaperBroker(balance=starting_balance)
    risk = RiskEngine(dna.risk)
    log = DecisionLog(log_path)
    bus = EventBus(history_limit=200_000)
    metrics = Metrics(starting_balance=starting_balance)
    trades: List[Trade] = []
    pos: Optional[OpenPosition] = None
    day: Optional[int] = None

    for i, candle in enumerate(candles):
        current_day = candle.ts // 86_400
        risk.new_session(broker.balance, is_new_day=day is None or current_day != day)
        day = current_day
        bus.publish(MarketEvent(ts=candle.ts, symbol=dna.symbol, candle=candle))

        if pos is not None:
            hit = _exit_for(pos, candle)
            if hit is not None:
                exit_px, exit_reason = hit
                _close(pos, broker, exit_px, exit_reason, candle.ts, risk, bus, trades)
                pos = None

        if pos is None:
            signal: Optional[Signal] = strat.evaluate(candles[: i + 1])
            if signal is not None:
                metrics.signals += 1
                bus.publish(
                    SignalEvent(
                        ts=candle.ts, symbol=dna.symbol, side=signal.side,
                        entry=signal.entry, stop=signal.stop, target=signal.target,
                        strategy=strat.name, reason=signal.reason,
                    )
                )
                decision = risk.evaluate(
                    symbol=dna.symbol, side=signal.side, entry=signal.entry,
                    stop=signal.stop, equity=broker.balance, ts=candle.ts,
                )
                bus.publish(
                    RiskDecisionEvent(
                        ts=candle.ts, symbol=dna.symbol, side=signal.side,
                        approved=decision.approved, units=decision.units,
                        risk_money=decision.risk_money, reason=decision.reason,
                    )
                )
                log.record(
                    DecisionRecord(
                        ts=candle.ts, symbol=dna.symbol, strategy=strat.name,
                        side=signal.side.value, entry=signal.entry, stop=signal.stop,
                        target=signal.target, units=decision.units,
                        risk_money=decision.risk_money, equity=broker.balance,
                        approved=decision.approved,
                        reason=f"{signal.reason} | risk: {decision.reason}",
                    )
                )
                if decision.approved:
                    metrics.approved += 1
                    bus.publish(
                        OrderEvent(ts=candle.ts, symbol=dna.symbol, side=signal.side,
                                   units=decision.units)
                    )
                    fill = broker.fill_entry(signal.side, decision.units, signal.entry)
                    bus.publish(
                        FillEvent(ts=candle.ts, symbol=dna.symbol, side=signal.side,
                                  units=decision.units, price=fill.price,
                                  commission=fill.commission)
                    )
                    pos = OpenPosition(
                        symbol=dna.symbol, side=signal.side, entry=fill.price,
                        stop=signal.stop, target=signal.target, units=decision.units,
                        opened_ts=candle.ts, strategy=strat.name,
                        entry_commission=fill.commission,
                    )
                    risk.register_open(dna.symbol, decision.units * fill.price)
                else:
                    metrics.rejected += 1

        metrics.equity_curve.append(broker.balance)

    # Close whatever is still open at the last price so pnl is not left floating.
    if pos is not None:
        _close(pos, broker, candles[-1].close, "end_of_data", candles[-1].ts,
               risk, bus, trades)
        if metrics.equity_curve:
            metrics.equity_curve[-1] = broker.balance

    metrics.trades = trades
    bus.history.clear()  # keep memory flat; the decision log is the durable record
    return BacktestRun(metrics=metrics, log=log, bus=bus, trades=trades)
