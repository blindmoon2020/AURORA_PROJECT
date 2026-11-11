"""The vertical slice: data -> strategy -> risk -> broker -> journal -> metrics.

Execution model, stated plainly because it decides the result:
  * a signal is generated on the close of bar i
  * the order fills at the OPEN of bar i+`execution_lag` (default 1), paying
    half the spread; there is no fill at the price that generated the signal
  * a bar that gaps through the stop fills at the open, not at the stop
  * a bar that touches both stop and target closes at the stop
  * stop fills take adverse slippage; target fills do not
  * commissions are charged on both legs and are inside trade pnl

Invariants asserted by the tests:
  final_equity == starting_balance + sum(trade.pnl)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
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
from ..strategies.base import Signal, Strategy, precompute
from ..strategies.dna import StrategyDna
from .metrics import Metrics, Trade, periods_per_year_for


@dataclass
class OpenPosition:
    symbol: str
    side: Side
    entry: float
    stop: float
    target: float
    units: float
    opened_ts: int
    opened_index: int
    strategy: str
    entry_commission: float
    risk_money: float
    decision_id: str = ""


@dataclass
class PendingOrder:
    signal: Signal
    units: float
    risk_money: float
    due_index: int
    symbol: str
    strategy: str
    decision_id: str = ""


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
    """Return (price, reason). Gap through the level fills at the open. Stop wins ties."""
    if pos.side is Side.LONG:
        if candle.open <= pos.stop:
            return candle.open, "stop_gap"
        if candle.low <= pos.stop:
            return pos.stop, "stop"
        if candle.open >= pos.target:
            return candle.open, "target_gap"
        if candle.high >= pos.target:
            return pos.target, "target"
    else:
        if candle.open >= pos.stop:
            return candle.open, "stop_gap"
        if candle.high >= pos.stop:
            return pos.stop, "stop"
        if candle.open <= pos.target:
            return candle.open, "target_gap"
        if candle.low <= pos.target:
            return pos.target, "target"
    return None


def _close(
    pos: OpenPosition,
    broker: PaperBroker,
    exit_price: float,
    exit_reason: str,
    ts: int,
    index: int,
    risk: RiskEngine,
    bus: EventBus,
    trades: List[Trade],
) -> Trade:
    fill = broker.fill_exit(
        pos.side, pos.units, exit_price, stop_like=exit_reason.startswith("stop")
    )
    gross = (fill.price - pos.entry) * pos.side.sign * pos.units
    broker.balance += gross - fill.commission
    pnl = gross - fill.commission - pos.entry_commission
    trade = Trade(
        symbol=pos.symbol,
        side=pos.side.value,
        entry=pos.entry,
        exit=fill.price,
        units=pos.units,
        pnl=pnl,
        r_multiple=pnl / pos.risk_money if pos.risk_money else 0.0,
        opened_ts=pos.opened_ts,
        closed_ts=ts,
        exit_reason=exit_reason,
        strategy=pos.strategy,
        bars_held=index - pos.opened_index,
        risk_money=pos.risk_money,
        decision_id=pos.decision_id,
    )
    trades.append(trade)
    risk.register_close(pos.symbol, pnl)
    bus.publish(
        ExitEvent(ts=ts, symbol=pos.symbol, price=fill.price, pnl=pnl, exit_reason=exit_reason)
    )
    return trade


def _infer_periods_per_year(candles: Sequence[Candle]) -> int:
    if len(candles) < 3:
        return 252
    deltas = sorted(b.ts - a.ts for a, b in zip(candles, candles[1:]) if b.ts > a.ts)
    if not deltas:
        return 252
    return periods_per_year_for(int(median(deltas)))


def run_backtest(
    candles: Sequence[Candle],
    dna: StrategyDna,
    strategy: Optional[Strategy] = None,
    starting_balance: float = 10_000.0,
    broker: Optional[PaperBroker] = None,
    log_path: Optional[str | Path] = None,
    execution_lag: int = 1,
    risk: Optional[RiskEngine] = None,
) -> BacktestRun:
    if not candles:
        raise ValueError("no candles to backtest")
    candles = list(candles)
    strat = strategy or dna.build()
    broker = broker or PaperBroker(balance=starting_balance)
    risk = risk or RiskEngine(dna.risk)
    log = DecisionLog(log_path)
    bus = EventBus(history_limit=50_000)
    metrics = Metrics(
        starting_balance=starting_balance,
        periods_per_year=_infer_periods_per_year(candles),
    )
    signal_map = precompute(strat, candles)
    trades: List[Trade] = []
    pos: Optional[OpenPosition] = None
    pending: Optional[PendingOrder] = None
    day: Optional[int] = None

    for i, candle in enumerate(candles):
        current_day = candle.ts // 86_400
        if day is None or current_day != day:
            risk.start_day(broker.balance)
        day = current_day
        bus.publish(MarketEvent(ts=candle.ts, symbol=dna.symbol, candle=candle))

        # 1. exits on this bar
        if pos is not None:
            hit = _exit_for(pos, candle)
            if hit is not None:
                price, reason = hit
                _close(pos, broker, price, reason, candle.ts, i, risk, bus, trades)
                pos = None

        # 2. fill the order that is due on this bar, at the open
        if pending is not None and pending.due_index <= i and pos is None:
            side = pending.signal.side
            fill = broker.fill_entry(side, pending.units, candle.open)
            bus.publish(
                FillEvent(ts=candle.ts, symbol=dna.symbol, side=side,
                          units=pending.units, price=fill.price, commission=fill.commission)
            )
            pos = OpenPosition(
                symbol=dna.symbol, side=side, entry=fill.price,
                stop=pending.signal.stop, target=pending.signal.target,
                units=pending.units, opened_ts=candle.ts, opened_index=i,
                strategy=pending.strategy, entry_commission=fill.commission,
                risk_money=pending.risk_money, decision_id=pending.decision_id,
            )
            risk.register_open(dna.symbol, pending.units * fill.price)
            pending = None
            # a stop or target can be hit on the entry bar itself
            hit = _exit_for(pos, candle)
            if hit is not None:
                price, reason = hit
                _close(pos, broker, price, reason, candle.ts, i, risk, bus, trades)
                pos = None

        # 3. new signal on the close of this bar
        if pos is None and pending is None:
            signal: Optional[Signal] = signal_map[i]
            if signal is not None:
                metrics.signals += 1
                bus.publish(
                    SignalEvent(ts=candle.ts, symbol=dna.symbol, side=signal.side,
                                entry=signal.entry, stop=signal.stop, target=signal.target,
                                strategy=strat.name, reason=signal.reason)
                )
                decision = risk.evaluate(
                    symbol=dna.symbol, side=signal.side, entry=signal.entry,
                    stop=signal.stop, equity=broker.balance, ts=candle.ts,
                )
                bus.publish(
                    RiskDecisionEvent(ts=candle.ts, symbol=dna.symbol, side=signal.side,
                                      approved=decision.approved, units=decision.units,
                                      risk_money=decision.risk_money, reason=decision.reason)
                )
                record = log.record(
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
                    pending = PendingOrder(
                        signal=signal, units=decision.units, risk_money=decision.risk_money,
                        due_index=i + max(1, execution_lag), symbol=dna.symbol,
                        strategy=strat.name, decision_id=record.decision_id,
                    )
                else:
                    metrics.rejected += 1

        # 4. curves
        metrics.equity_curve.append(broker.balance)
        if pos is not None:
            unrealized = (candle.close - pos.entry) * pos.side.sign * pos.units
            metrics.mtm_curve.append(broker.balance + unrealized)
        else:
            metrics.mtm_curve.append(broker.balance)
        risk.observe_equity(broker.balance)

    if pending is not None and pos is None:
        # order never filled: no trade, but the decision stands in the log
        pass

    if pos is not None:
        _close(pos, broker, candles[-1].close, "end_of_data", candles[-1].ts,
               len(candles) - 1, risk, bus, trades)
        if metrics.equity_curve:
            metrics.equity_curve[-1] = broker.balance
            metrics.mtm_curve[-1] = broker.balance

    # per-bar returns on the mark-to-market curve, for Sharpe and friends
    curve = metrics.mtm_curve
    prev = starting_balance
    returns = []
    for eq in curve:
        returns.append((eq / prev - 1.0) if prev > 0 else 0.0)
        prev = eq
    metrics.bar_returns = returns
    metrics.trades = trades
    bus.history.clear()
    return BacktestRun(metrics=metrics, log=log, bus=bus, trades=trades)
