import random
import unittest

from aurora import stats
from aurora.backtest import run_backtest
from aurora.data import clean_candles, synthetic_candles
from aurora.strategies import load_dna
from aurora.validation import cscv_pbo, make_folds, run_walk_forward
from pathlib import Path

DNA_PATH = Path(__file__).resolve().parents[1] / "strategies" / "ema_cross_eurusd.json"


class FoldTests(unittest.TestCase):
    def test_folds_do_not_overlap_and_respect_embargo(self):
        folds = make_folds(4000, n_folds=5, is_fraction=0.75, embargo_bars=8)
        self.assertEqual(len(folds), 5)
        for f in folds:
            self.assertLessEqual(f.is_start, f.is_end)
            self.assertLessEqual(f.is_end, f.oos_start - 7)  # embargo respected
            self.assertLess(f.oos_start, f.oos_end)
        for a, b in zip(folds, folds[1:]):
            self.assertLessEqual(a.oos_end, b.oos_start)

    def test_short_series_is_rejected(self):
        with self.assertRaises(ValueError):
            make_folds(50, n_folds=5)


class WalkForwardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dna = load_dna(DNA_PATH)
        cls.candles = synthetic_candles(n=2400, seed=21)
        cls.grid = {"fast": [8, 20], "slow": [34, 50]}
        cls.result = run_walk_forward(cls.candles, cls.dna, cls.grid, n_folds=3,
                                      min_trades=2)

    def test_produces_out_of_sample_trades(self):
        self.assertGreaterEqual(len(self.result.folds), 2)
        self.assertEqual(self.result.oos_metrics.count, len(self.result.oos_trades))

    def test_every_fold_choice_comes_from_the_grid(self):
        for fold in self.result.folds:
            self.assertIn(fold.best_params.get("fast"), self.grid["fast"])
            self.assertIn(fold.best_params.get("slow"), self.grid["slow"])

    def test_trials_are_recorded_for_deflation(self):
        self.assertGreater(len(self.result.trial_srs), 1)

    def test_oos_equity_matches_oos_trades(self):
        m = self.result.oos_metrics
        expected = m.starting_balance + sum(t.pnl for t in self.result.oos_trades)
        self.assertAlmostEqual(m.final_equity, expected, places=6)


class PboTests(unittest.TestCase):
    def test_pure_noise_has_a_high_pbo(self):
        rng = random.Random(3)
        rows = [[rng.gauss(0, 0.001) for _ in range(1200)] for _ in range(8)]
        out = cscv_pbo(rows, n_splits=8)
        self.assertGreater(out["pbo"], 0.25)
        self.assertLessEqual(out["pbo"], 1.0)

    def test_dominant_config_is_not_overfit(self):
        rng = random.Random(5)
        rows = [[rng.gauss(0, 0.001) for _ in range(1200)] for _ in range(5)]
        edge = [0.0015 + rng.gauss(0, 0.001) for _ in range(1200)]
        out = cscv_pbo([edge] + rows, n_splits=8)
        self.assertLess(out["pbo"], 0.2)

    def test_mismatched_lengths_rejected(self):
        with self.assertRaises(ValueError):
            cscv_pbo([[0.1] * 10, [0.1] * 9])


class StatsTests(unittest.TestCase):
    def test_t_p_value_matches_known_values(self):
        self.assertAlmostEqual(stats.t_p_value(2.228, 10), 0.05, places=3)
        self.assertAlmostEqual(stats.t_p_value(2.0, 10), 0.0734, places=3)

    def test_more_trials_lowers_deflated_sharpe(self):
        rng = random.Random(11)
        returns = [rng.gauss(0.0004, 0.004) for _ in range(800)]
        few = stats.deflated_sharpe_ratio(returns, [0.05, 0.06])["dsr"]
        many = stats.deflated_sharpe_ratio(returns, [0.05 + 0.01 * i for i in range(200)])["dsr"]
        self.assertLess(many, few)

    def test_psr_is_a_probability(self):
        rng = random.Random(2)
        returns = [rng.gauss(0.0002, 0.003) for _ in range(500)]
        self.assertTrue(0.0 <= stats.probabilistic_sharpe_ratio(returns) <= 1.0)


class DataValidationTests(unittest.TestCase):
    def test_fx_weekend_is_not_counted_as_missing(self):
        # 09:00 UTC Monday to 09:00 UTC Friday, hourly: no gaps should be reported
        from datetime import datetime, timezone
        base = datetime(2026, 3, 2, 0, 0, tzinfo=timezone.utc)  # Monday
        candles = []
        ts = int(base.timestamp())
        for i in range(5 * 24):  # Mon 00:00 .. Fri 23:00
            candles.append(synthetic_candles(n=1, seed=i, start=1.10)[0].__class__(
                ts=ts + i * 3600, open=1.10, high=1.101, low=1.099, close=1.10))
        clean, report = clean_candles(candles, profile="fx")
        self.assertEqual(report.missing_bars, 0)
        self.assertGreater(report.coverage_pct, 99.0)

    def test_duplicates_and_zero_range_are_removed(self):
        base = synthetic_candles(n=10, seed=1)
        from aurora.core.types import Candle
        dup = list(base) + [base[3], Candle(ts=base[5].ts + 900, open=1.1,
                                            high=1.1, low=1.1, close=1.1)]
        clean, report = clean_candles(dup)
        self.assertEqual(report.duplicates, 1)
        self.assertEqual(report.zero_range, 1)
        self.assertEqual(len(clean), 10)

    def test_clean_series_is_clean(self):
        candles = synthetic_candles(n=500, seed=9)
        clean, report = clean_candles(candles, profile="crypto")
        self.assertEqual(report.duplicates, 0)
        self.assertEqual(report.zero_range, 0)
        self.assertEqual(report.coverage_pct, 100.0)


if __name__ == "__main__":
    unittest.main()
