"""Execution realism: lag, gap fills, slippage, tie-breaking."""
import unittest

from aurora.backtest import run_backtest
from aurora.core.types import Candle, Side
from aurora.execution.paper import PaperBroker
from aurora.strategies.base import Signal
from aurora.strategies.dna import parse_dna

DNA = parse_dna({
    "name": "test", "symbol": "EURUSD", "type": "ema_cross",
    "params": {"fast": 2, "slow": 3},
    "risk": {"risk_per_trade_pct": 0.5, "daily_loss_cap_pct": 20.0,
             "max_open_positions": 1, "max_leverage": 30.0,
             "max_daily_trades": 99, "max_total_drawdown_pct": 50.0},
})


class OneShot:
    """Emits a single signal at a chosen bar index; the rest is flat."""

    name = "oneshot"

    def __init__(self, at: int, side: Side, entry: float, stop: float, target: float):
        self.at, self.side, self.entry, self.stop, self.target = at, side, entry, stop, target

    def warmup(self) -> int:
        return 1

    def prepare(self, candles):
        out = [None] * len(candles)
        if self.at < len(candles):
            out[self.at] = Signal(self.side, self.entry, self.stop, self.target, "test signal")
        return out

    def evaluate(self, candles):
        return None


def flat_bar(ts, price, spike_hi=None, spike_lo=None, open_=None):
    o = price if open_ is None else open_
    hi = max(o, price, spike_hi if spike_hi is not None else price)
    lo = min(o, price, spike_lo if spike_lo is not None else price)
    return Candle(ts=ts, open=o, high=hi, low=lo, close=price)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.broker = PaperBroker(balance=10_000.0, spread=0.00002,
                                  commission_per_unit=0.0, slippage=0.00001)

    def test_fill_happens_at_next_open_not_at_signal_price(self):
        candles = [flat_bar(i * 3600, 1.10) for i in range(6)]
        candles[3] = flat_bar(3 * 3600, 1.11, open_=1.12)   # next open gaps up
        strat = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.09, target=1.20)
        run = run_backtest(candles, DNA, strategy=strat, broker=self.broker,
                           execution_lag=1)
        self.assertEqual(len(run.trades), 1)
        entry = run.trades[0].entry
        # filled at bar 3 open (1.12) plus half the spread, never at 1.10
        self.assertAlmostEqual(entry, 1.12 + 0.00001, places=9)

    def test_gap_through_the_stop_fills_at_the_open(self):
        candles = [flat_bar(i * 3600, 1.10) for i in range(6)]
        candles[3] = flat_bar(3 * 3600, 1.10, open_=1.105)
        candles[4] = flat_bar(4 * 3600, 1.075, open_=1.08)   # gap below the 1.09 stop
        strat = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.09, target=1.20)
        run = run_backtest(candles, DNA, strategy=strat, broker=self.broker)
        trade = run.trades[0]
        self.assertEqual(trade.exit_reason, "stop_gap")
        # worse than the stop: open, minus half spread, minus slippage
        self.assertAlmostEqual(trade.exit, 1.08 - 0.00001 - 0.00001, places=9)
        self.assertLess(trade.pnl, -120)  # far worse than a clean stop at 1.09 (-75)

    def test_stop_wins_when_both_levels_are_touched(self):
        candles = [flat_bar(i * 3600, 1.10) for i in range(6)]
        candles[3] = flat_bar(3 * 3600, 1.10, open_=1.10)
        candles[4] = flat_bar(4 * 3600, 1.10, spike_hi=1.25, spike_lo=1.05)
        strat = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.09, target=1.20)
        run = run_backtest(candles, DNA, strategy=strat, broker=self.broker)
        self.assertEqual(run.trades[0].exit_reason, "stop")

    def test_slippage_makes_stops_more_expensive_than_no_slippage(self):
        candles = [flat_bar(i * 3600, 1.10) for i in range(8)]
        candles[3] = flat_bar(3 * 3600, 1.10, open_=1.10)
        candles[4] = flat_bar(4 * 3600, 1.08, spike_lo=1.085)
        strat = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.09, target=1.20)

        no_slip = PaperBroker(balance=10_000.0, spread=0.00002, slippage=0.0)
        with_slip = PaperBroker(balance=10_000.0, spread=0.00002, slippage=0.0002)
        a = run_backtest(candles, DNA, strategy=strat, broker=no_slip)
        b = run_backtest(candles, DNA, strategy=strat, broker=with_slip)
        self.assertLess(b.trades[0].pnl, a.trades[0].pnl - 0.5)

    def test_higher_lag_costs_more_than_lower_lag(self):
        # a steadily rising market: entering later is worse for a long
        candles = [flat_bar(i * 3600, 1.10 + i * 0.001) for i in range(10)]
        strat = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.08, target=1.30)
        lag1 = run_backtest(candles, DNA, strategy=strat,
                            broker=PaperBroker(balance=10_000.0))
        strat2 = OneShot(at=2, side=Side.LONG, entry=1.10, stop=1.08, target=1.30)
        lag2 = run_backtest(candles, DNA, strategy=strat2,
                            broker=PaperBroker(balance=10_000.0), execution_lag=3)
        self.assertGreater(lag2.trades[0].entry, lag1.trades[0].entry)


if __name__ == "__main__":
    unittest.main()
