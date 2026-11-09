import tempfile
import unittest
from pathlib import Path

from aurora.backtest import run_backtest
from aurora.data import synthetic_candles
from aurora.journal import read_log
from aurora.strategies import load_dna

DNA_PATH = Path(__file__).resolve().parents[1] / "strategies" / "ema_cross_eurusd.json"


class BacktestInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dna = load_dna(DNA_PATH)
        cls.candles = synthetic_candles(n=3000, seed=11)
        cls.result = run_backtest(cls.candles, cls.dna, starting_balance=10_000.0)

    def test_it_actually_trades(self):
        self.assertGreater(self.result.metrics.signals, 0)
        self.assertGreater(self.result.metrics.approved, 0)
        self.assertGreater(self.result.metrics.count, 0)

    def test_every_signal_has_a_decision(self):
        m = self.result.metrics
        self.assertEqual(m.approved + m.rejected, m.signals)
        self.assertEqual(len(self.result.log), m.signals)

    def test_every_decision_has_a_reason(self):
        for record in self.result.log.records:
            self.assertTrue(record.reason.strip(), record)
            self.assertIn("risk:", record.reason)

    def test_approved_decisions_are_sized(self):
        for record in self.result.log.approved():
            self.assertGreater(record.units, 0)
            self.assertGreater(record.risk_money, 0)
        for record in self.result.log.rejected():
            self.assertEqual(record.units, 0.0)

    def test_no_trade_risks_more_than_the_limit(self):
        limit = self.dna.risk.risk_per_trade_pct / 100.0
        for record in self.result.log.approved():
            # risk_money is recorded to the cent, so allow one cent of rounding up.
            self.assertLessEqual(record.risk_money, record.equity * limit + 0.01)

    def test_equity_accounting_is_exact(self):
        expected = self.result.metrics.starting_balance + sum(t.pnl for t in self.result.trades)
        self.assertAlmostEqual(self.result.metrics.final_equity, expected, places=6)

    def test_trades_are_well_formed(self):
        for t in self.result.trades:
            self.assertGreater(t.units, 0)
            self.assertIn(t.side, ("long", "short"))
            self.assertIn(t.exit_reason, ("stop", "target", "end_of_data"))
            self.assertGreaterEqual(t.closed_ts, t.opened_ts)

    def test_drawdown_is_a_percentage(self):
        self.assertGreaterEqual(self.result.metrics.max_drawdown_pct, 0.0)
        self.assertLessEqual(self.result.metrics.max_drawdown_pct, 100.0)

    def test_runs_are_deterministic(self):
        again = run_backtest(self.candles, self.dna, starting_balance=10_000.0)
        self.assertEqual(len(again.trades), len(self.result.trades))
        for a, b in zip(again.trades, self.result.trades):
            self.assertAlmostEqual(a.pnl, b.pnl, places=9)
        self.assertAlmostEqual(again.metrics.final_equity, self.result.metrics.final_equity, places=9)


class BacktestLoggingTests(unittest.TestCase):
    def test_decision_log_is_written_to_disk(self):
        dna = load_dna(DNA_PATH)
        candles = synthetic_candles(n=1200, seed=5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.jsonl"
            result = run_backtest(candles, dna, log_path=path)
            records = read_log(path)
        self.assertEqual(len(records), result.metrics.signals)
        self.assertGreater(len(records), 0)

    def test_empty_data_is_an_error(self):
        dna = load_dna(DNA_PATH)
        with self.assertRaises(ValueError):
            run_backtest([], dna)


if __name__ == "__main__":
    unittest.main()
