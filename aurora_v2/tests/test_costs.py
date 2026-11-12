import unittest
from datetime import datetime, timezone

from aurora.backtest import run_backtest
from aurora.core.types import Candle, Side
from aurora.execution import PaperBroker
from aurora.execution.costs import (SwapTable, is_triple_swap_day, swap_cost)
from aurora.strategies import parse_dna


class SwapMathTests(unittest.TestCase):
    def test_cost_is_pro_rata(self):
        # 2% a year on 100k for one day = 5.48
        self.assertAlmostEqual(swap_cost(100_000, 2.0, 1), 5.4795, places=3)
        self.assertAlmostEqual(swap_cost(100_000, 2.0, 365), 2_000.0, places=6)

    def test_negative_rate_is_a_credit(self):
        self.assertLess(swap_cost(100_000, -1.85, 1), 0)

    def test_positive_rate_is_the_normal_case(self):
        self.assertGreater(swap_cost(100_000, 3.15, 1), 0)

    def test_triple_swap_is_wednesday_and_configurable(self):
        wed = int(datetime(2026, 11, 11, tzinfo=timezone.utc).timestamp())
        mon = int(datetime(2026, 11, 9, tzinfo=timezone.utc).timestamp())
        fri = int(datetime(2026, 11, 13, tzinfo=timezone.utc).timestamp())
        self.assertTrue(is_triple_swap_day(wed))
        self.assertFalse(is_triple_swap_day(mon))
        self.assertTrue(is_triple_swap_day(fri, triple_weekday=4))

    def test_uncalibrated_table_charges_nothing(self):
        broker = PaperBroker(balance=10_000, swap=SwapTable())
        self.assertEqual(broker.charge_swap("EURUSD", Side.LONG, 10_000, 1.1, 3), 0.0)
        self.assertEqual(broker.balance, 10_000)

    def test_calibrated_table_charges(self):
        table = SwapTable.from_pairs([("EURUSD", 1.85, 0.5)], source="demo")
        broker = PaperBroker(balance=10_000, swap=table)
        cost = broker.charge_swap("EURUSD", Side.LONG, 10_000, 1.1, 1)
        self.assertGreater(cost, 0)
        self.assertAlmostEqual(broker.balance, 10_000 - cost, places=9)


class OneShot:
    """Emits one long signal at a fixed bar, for execution tests."""

    name = "one_shot"

    def __init__(self, at: int, entry: float, stop: float, target: float):
        self.at, self.entry, self.stop, self.target = at, entry, stop, target

    def warmup(self) -> int:
        return 1

    def prepare(self, candles):
        from aurora.strategies.base import Signal
        out = [None] * len(candles)
        if self.at < len(out):
            out[self.at] = Signal(side=Side.LONG, entry=self.entry, stop=self.stop,
                                  target=self.target, reason="one shot")
        return out


class SwapInRunnerTests(unittest.TestCase):
    def _dna(self):
        return parse_dna({"name": "t", "symbol": "EURUSD", "type": "ema_cross",
                          "params": {"fast": 2, "slow": 3, "stop_lookback": 1, "rr": 2.0},
                          "risk": {"risk_per_trade_pct": 0.5, "daily_loss_cap_pct": 2.0,
                                   "max_open_positions": 1}})

    def _candles(self, n=8):
        out, day = [], 86_400 * 20_000
        for i in range(n):
            px = 1.10 + 0.001 * i
            out.append(Candle(ts=day + i * 86_400, open=px, high=px + 0.002,
                              low=px - 0.002, close=px))
        return out

    def test_swap_reduces_pnl_and_accounting_still_closes(self):
        candles = self._candles()
        strat = OneShot(at=0, entry=1.101, stop=1.050, target=9.0)
        plain = run_backtest(candles, self._dna(), strategy=strat, starting_balance=10_000)
        table = SwapTable.from_pairs([("EURUSD", 5.0, 5.0)], source="test")
        with_swap = run_backtest(candles, self._dna(), strategy=strat, starting_balance=10_000,
                                 broker=PaperBroker(balance=10_000, swap=table))
        self.assertEqual(len(with_swap.trades), 1)
        self.assertLess(with_swap.trades[0].pnl, plain.trades[0].pnl)
        # the invariant that matters: final equity equals start plus the pnl booked
        booked = sum(t.pnl for t in with_swap.trades)
        self.assertAlmostEqual(with_swap.metrics.final_equity, 10_000 + booked, places=6)


if __name__ == "__main__":
    unittest.main()
