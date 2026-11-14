import unittest

from aurora.execution.impact import DEFAULT_K, calibrate_k, sliced_cost_money
from aurora.execution.reconcile import Break, reconcile, require_clean
from aurora.portfolio.risk_budget import covariance_matrix, shrunk_covariance
from aurora.portfolio.scenarios import (SCENARIOS, class_of, crisis_exposure_cap,
                                        margin_of_safety, replay, replay_all,
                                        reverse_stress, tail_loss)


class ScenarioTests(unittest.TestCase):
    def test_a_levered_equity_book_loses_in_2008(self):
        r = replay({"AAPL": 0.5, "SPY": 0.5}, "۲۰۰۸ بحران مالی")
        self.assertLess(r.loss_pct, -30)

    def test_an_unknown_symbol_is_treated_as_equity(self):
        self.assertEqual(class_of("ZZZZ"), "equity")

    def test_bonds_and_gold_are_classified_from_their_tickers(self):
        self.assertEqual(class_of("TLT"), "bonds")
        self.assertEqual(class_of("GLD"), "gold")
        self.assertEqual(class_of("BTC-USD"), "crypto")

    def test_gold_holds_up_when_equities_fall(self):
        eq = replay({"AAPL": 1.0}, "۲۰۰۸ بحران مالی")
        au = replay({"GLD": 1.0}, "۲۰۰۸ بحران مالی")
        self.assertGreater(au.loss_pct, eq.loss_pct)

    def test_an_empty_book_loses_nothing(self):
        self.assertEqual(replay({}, "۲۰۰۸ بحران مالی").loss_pct, 0.0)

    def test_unknown_scenario_raises_instead_of_returning_zero(self):
        with self.assertRaises(KeyError):
            replay({"AAPL": 1.0}, "سناریوی ناموجود")

    def test_limit_breach_is_flagged(self):
        r = replay({"AAPL": 1.0}, "۲۰۲۰ کووید", limit_pct=20)
        self.assertTrue(r.breaches_limit)

    def test_replay_all_covers_every_named_crisis(self):
        self.assertEqual(len(replay_all({"AAPL": 1.0})), len(SCENARIOS))

    def test_reverse_stress_finds_the_breaking_shock(self):
        shock = reverse_stress({"AAPL": 0.30}, limit_pct=10)
        self.assertAlmostEqual(shock * 30.0, 10.0, places=2)

    def test_a_small_book_needs_a_bigger_shock(self):
        self.assertGreater(reverse_stress({"AAPL": 0.10}, 10), reverse_stress({"AAPL": 0.50}, 10))

    def test_reverse_stress_of_an_empty_book_is_full_loss(self):
        self.assertEqual(reverse_stress({}, 10), 1.0)

    def test_margin_of_safety_reports_both_numbers(self):
        m = margin_of_safety({"AAPL": 0.5}, 20)
        self.assertGreater(m["shock_to_breach_pct"], 0)
        self.assertLess(m["worst_scenario_pct"], 0)

    def test_fat_tail_is_worse_than_the_gaussian_one(self):
        self.assertLess(tail_loss({"AAPL": 1.0}, 0.01, 21, df=3),
                        tail_loss({"AAPL": 1.0}, 0.01, 21, df=50))


class ExposureCapTests(unittest.TestCase):
    def test_a_book_that_breaks_the_limit_gets_scaled_down(self):
        # 130% gross equity-ish book, 2008 replay near -49%, limit 40% -> scale below 1
        weights = {f"S{i}": 0.13 for i in range(10)}
        cap = crisis_exposure_cap(weights, 40)
        self.assertLess(cap["scale"], 1.0)
        # the loss itself scales with gross, so loss * scale must land on the limit
        self.assertAlmostEqual(abs(cap["worst_loss_pct"]) * cap["scale"], 40.0, delta=0.5)

    def test_a_small_book_is_not_scaled(self):
        self.assertEqual(crisis_exposure_cap({"GLD": 0.1}, 40)["scale"], 1.0)

    def test_the_binding_scenario_is_named(self):
        weights = {f"S{i}": 0.13 for i in range(10)}
        self.assertIn(crisis_exposure_cap(weights, 40)["binding_scenario"], SCENARIOS)


class ShrinkageTests(unittest.TestCase):
    def _series(self, n):
        return {"a": [0.01, -0.008, 0.012, 0.004, -0.003][:n] * 30,
                "b": [-0.002, 0.003, -0.001, 0.002, 0.001][:n] * 30}

    def test_shrinking_pulls_extreme_correlations_toward_the_average(self):
        series = self._series(5)
        raw, shrunk = covariance_matrix(series), shrunk_covariance(series)
        import math
        raw_corr = raw["a"]["b"] / math.sqrt(raw["a"]["a"] * raw["b"]["b"])
        shr_corr = shrunk["a"]["b"] / math.sqrt(shrunk["a"]["a"] * shrunk["b"]["b"])
        self.assertLess(abs(shr_corr), abs(raw_corr) + 1e-12)

    def test_diagonal_variances_are_untouched(self):
        series = self._series(5)
        raw, shrunk = covariance_matrix(series), shrunk_covariance(series)
        self.assertAlmostEqual(raw["a"]["a"], shrunk["a"]["a"])

    def test_a_single_asset_series_passes_through(self):
        self.assertEqual(shrunk_covariance({"a": [0.01, -0.01] * 10}), covariance_matrix({"a": [0.01, -0.01] * 10}))


class CalibrateKTests(unittest.TestCase):
    def test_too_few_fills_keeps_the_assumption(self):
        out = calibrate_k([(0.01, 100, 10)] * 3)
        self.assertIsNone(out["k"])
        self.assertIn("insufficient", out["verdict"])

    def test_k_is_recovered_from_consistent_fills(self):
        obs = [(0.01, 100.0, DEFAULT_K * 100.0 * 0.1)] * 12
        out = calibrate_k(obs)
        self.assertAlmostEqual(out["k"], DEFAULT_K, places=6)

    def test_zero_volatility_fills_are_ignored_not_divided_by(self):
        out = calibrate_k([(0.01, 0.0, 5.0)] * 20)
        self.assertIsNone(out["k"])

    def test_sliced_cost_is_reported_in_money(self):
        cost = sliced_cost_money(3e7, 1e8, 100)
        self.assertIsNotNone(cost)
        self.assertGreater(cost, 0)


class ReconcileTests(unittest.TestCase):
    def test_identical_books_reconcile(self):
        rep = reconcile({"AAPL": 10}, {"AAPL": 10}, 100.0, 100.0)
        self.assertTrue(rep.clean)
        self.assertFalse(rep.blocks_trading)

    def test_a_position_the_broker_does_not_have_is_missing(self):
        rep = reconcile({"AAPL": 10}, {})
        self.assertEqual(rep.breaks[0].kind, "missing")

    def test_a_position_we_do_not_know_about_is_phantom(self):
        rep = reconcile({}, {"TSLA": 3})
        self.assertEqual(rep.breaks[0].kind, "phantom")

    def test_a_size_difference_is_a_break(self):
        rep = reconcile({"AAPL": 10}, {"AAPL": 9})
        self.assertEqual(rep.breaks[0].kind, "size")

    def test_cash_difference_beyond_tolerance_is_a_break(self):
        rep = reconcile({"AAPL": 10}, {"AAPL": 10}, 100.0, 90.0)
        self.assertEqual(rep.breaks[0].kind, "cash")

    def test_cash_within_tolerance_is_fine(self):
        self.assertTrue(reconcile({"A": 1}, {"A": 1}, 100.0, 100.005).clean)

    def test_require_clean_refuses_to_trade_on_a_broken_book(self):
        with self.assertRaises(RuntimeError):
            require_clean(reconcile({"AAPL": 10}, {}))

    def test_summary_names_the_break_types(self):
        rep = reconcile({"AAPL": 10}, {"TSLA": 1})
        self.assertIn("missing", rep.summary())
        self.assertIn("phantom", rep.summary())


if __name__ == "__main__":
    unittest.main()
