import unittest

from aurora.portfolio.brakes import (OverlayDecision, apply_overlay, decide,
                                      drawdown_scale, vol_target_scale)


class VolTargetTests(unittest.TestCase):
    def test_risk_above_target_shrinks_exposure(self):
        self.assertAlmostEqual(vol_target_scale(0.20, 0.12), 0.60)

    def test_risk_below_target_never_levers(self):
        self.assertEqual(vol_target_scale(0.06, 0.12), 1.0)

    def test_missing_volatility_means_no_position(self):
        self.assertEqual(vol_target_scale(0.0, 0.12), 0.0)

    def test_a_floor_stops_the_scale_reaching_zero(self):
        self.assertGreaterEqual(vol_target_scale(10.0, 0.12), 0.30)


class DrawdownTests(unittest.TestCase):
    def test_above_the_soft_trigger_nothing_happens(self):
        self.assertEqual(drawdown_scale(5.0), 1.0)

    def test_at_the_hard_trigger_the_floor_applies(self):
        self.assertEqual(drawdown_scale(20.0), 0.25)

    def test_between_the_triggers_it_is_linear_and_monotone(self):
        mid = drawdown_scale(15.0)
        self.assertTrue(0.25 < mid < 1.0)
        self.assertGreater(drawdown_scale(12.0), drawdown_scale(18.0))

    def test_drawdown_sign_does_not_matter(self):
        self.assertEqual(drawdown_scale(-15.0), drawdown_scale(15.0))


class DecideTests(unittest.TestCase):
    def test_the_tightest_brake_governs_not_the_average(self):
        d = decide({"AAPL": 1.0}, current_vol=0.20, target_vol=0.12, drawdown_pct=18.0)
        self.assertEqual(d.binding, "drawdown")
        self.assertAlmostEqual(d.scale, d.parts["drawdown"])

    def test_scale_never_exceeds_one(self):
        d = decide({"AAPL": 0.05}, current_vol=0.02, target_vol=0.12)
        self.assertLessEqual(d.scale, 1.0)

    def test_a_breaking_crisis_scenario_is_reported_as_the_cause(self):
        d = decide({f"S{i}": 0.13 for i in range(10)}, limit_pct=40)
        self.assertEqual(d.binding, "crisis")
        self.assertTrue(any("سقف بحران" in n for n in d.notes))

    def test_reserved_sleeve_budget_is_counted_in_the_crisis_replay(self):
        # 100% equity targets alone survive 2008 inside a 40% limit; adding the sleeve's
        # reserved 30% pushes the replay past it, and the brake must see that
        plain = decide({f"S{i}": 0.10 for i in range(10)}, limit_pct=40)
        reserved = decide({f"S{i}": 0.10 for i in range(10)}, limit_pct=40,
                          reserved_exposure=0.30)
        self.assertEqual(plain.scale, 1.0)
        self.assertLess(reserved.scale, 1.0)

    def test_no_inputs_is_full_scale_not_silence(self):
        d = decide({})
        self.assertEqual(d.scale, 1.0)
        self.assertEqual(d.binding, "هیچ")

    def test_apply_overlay_scales_every_target(self):
        d = OverlayDecision(0.5, "vol", {"vol": 0.5})
        self.assertEqual(apply_overlay({"A": 0.2, "B": 0.1}, d), {"A": 0.1, "B": 0.05})

    def test_overlay_never_produces_a_position_above_its_target(self):
        d = OverlayDecision(0.816, "crisis", {"crisis": 0.816})
        out = apply_overlay({"A": 0.30}, d)
        self.assertLessEqual(out["A"], 0.30)


if __name__ == "__main__":
    unittest.main()


class SmoothingTests(unittest.TestCase):
    """De-risk at once, re-risk slowly: safety costs nothing, cheapness costs a deadband."""

    def test_no_previous_scale_takes_the_new_one(self):
        from aurora.portfolio.brakes import smoothed_scale
        self.assertEqual(smoothed_scale(0.81, None), 0.81)

    def test_a_cut_is_taken_immediately_however_small(self):
        from aurora.portfolio.brakes import smoothed_scale
        self.assertEqual(smoothed_scale(0.98, 1.0), 0.98)

    def test_a_small_rise_is_ignored_to_avoid_churn(self):
        from aurora.portfolio.brakes import smoothed_scale
        self.assertEqual(smoothed_scale(1.0, 0.97), 0.97)

    def test_a_meaningful_rise_is_taken(self):
        from aurora.portfolio.brakes import smoothed_scale
        self.assertEqual(smoothed_scale(1.0, 0.90), 1.0)

    def test_the_deadband_is_reported_not_hidden(self):
        d = decide({f"S{i}": 0.10 for i in range(10)}, limit_pct=40,
                   reserved_exposure=0.30, previous_scale=0.80)
        self.assertAlmostEqual(d.scale, 0.80, places=6)
        self.assertTrue(any("نگه داشته شد" in n for n in d.notes))
