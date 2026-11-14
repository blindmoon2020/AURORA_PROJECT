import unittest

from aurora.backtest.harness import study_report, walk_forward_select
from aurora.execution.fee_schedule import (FX_MAJOR, IRAN_TSETMC, US_LARGE_CAP,
                                           cost_sensitivity)


class FeeTests(unittest.TestCase):
    def test_round_trip_adds_the_three_components(self):
        self.assertAlmostEqual(US_LARGE_CAP.round_trip_bps(), 4.0, places=6)
        self.assertAlmostEqual(US_LARGE_CAP.cost_rate(), 0.0004, places=8)

    def test_iran_is_much_more_expensive_than_us(self):
        self.assertGreater(IRAN_TSETMC.cost_rate(), 10 * US_LARGE_CAP.cost_rate())

    def test_trade_cost_scales_with_notional_and_charges_tax_once(self):
        small = IRAN_TSETMC.trade_cost(10_000)
        big = IRAN_TSETMC.trade_cost(20_000)
        self.assertAlmostEqual(big, 2 * small, places=6)

    def test_minimum_commission_binds_on_a_tiny_trade(self):
        from aurora.execution.fee_schedule import FeeSchedule
        s = FeeSchedule("x", commission_bps_per_side=1.0, min_commission=1.0)
        self.assertAlmostEqual(s.trade_cost(100), 2.0, places=6)

    def test_sensitivity_spans_a_range_around_the_base(self):
        trip = cost_sensitivity(FX_MAJOR)
        self.assertEqual([m for m, _ in trip], [0.5, 1.0, 2.0, 4.0])
        self.assertAlmostEqual(trip[1][1], FX_MAJOR.cost_rate(), places=10)


class HarnessTests(unittest.TestCase):
    def _series(self):
        good = [0.02, 0.01, 0.015] * 30
        bad = [-0.01, -0.02, -0.005] * 30
        return {"good": good, "bad": bad}

    def test_chooses_the_better_config_on_the_past(self):
        oos, picks = walk_forward_select(self._series())
        self.assertTrue(oos)
        self.assertTrue(all(p == "good" for p in picks))

    def test_report_carries_a_verdict_and_deflation(self):
        rep = study_report(self._series(), label="unit")
        self.assertEqual(rep["label"], "unit")
        self.assertIsNotNone(rep["verdict"])
        self.assertGreater(rep["sharpe"], 0.0)
        self.assertIn("pbo", rep)

    def test_short_history_is_refused_not_guessed(self):
        rep = study_report({"a": [0.01] * 10, "b": [0.0] * 10})
        self.assertIsNone(rep["verdict"])
        self.assertIn("shorter", rep["reason"])

    def test_unequal_lengths_are_an_error(self):
        with self.assertRaises(ValueError):
            walk_forward_select({"a": [0.01] * 50, "b": [0.01] * 40})


if __name__ == "__main__":
    unittest.main()
