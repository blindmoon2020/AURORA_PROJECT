import unittest

from aurora.signals.factors import RankedAsset
from aurora.signals.macro import point_in_time, regime, tilt

DAY = 86400


class RegimeTests(unittest.TestCase):
    def test_calm_market_is_supportive(self):
        r = regime(vix=12, curve_bp=120, credit_bp=300, real_rate=-0.5)
        self.assertGreater(r.score, 0.25)
        self.assertEqual(r.label, "supportive")

    def test_stress_is_hostile(self):
        r = regime(vix=40, curve_bp=-30, credit_bp=800, real_rate=3.0)
        self.assertLess(r.score, -0.25)
        self.assertEqual(r.label, "hostile")

    def test_unknown_inputs_are_ignored_not_assumed(self):
        r = regime(vix=None, curve_bp=100, credit_bp=None, real_rate=None)
        self.assertEqual(r.label, "supportive")
        self.assertIsNone(r.inputs["vix"])

    def test_all_unknown_is_neutral_unknown(self):
        r = regime(None, None, None, None)
        self.assertEqual(r.score, 0.0)
        self.assertEqual(r.label, "unknown")

    def test_inverted_curve_is_not_supportive(self):
        r = regime(vix=20, curve_bp=-10, credit_bp=400, real_rate=1.0)
        self.assertLessEqual(r.score, 0.0)


class TiltTests(unittest.TestCase):
    def test_hostile_backdrop_shrinks_scores_without_reordering(self):
        ranked = [RankedAsset("A", 1.0, {}, "x"), RankedAsset("B", -1.0, {}, "y")]
        out = tilt(ranked, regime(40, -30, 800, 3.0))
        self.assertEqual([r.symbol for r in out], ["A", "B"])
        self.assertLess(abs(out[0].score), 1.0)
        self.assertLess(abs(out[1].score), 1.0)

    def test_supportive_backdrop_lifts_scores(self):
        ranked = [RankedAsset("A", 1.0, {}, "x")]
        out = tilt(ranked, regime(10, 150, 250, -1.0))
        self.assertGreater(out[0].score, 1.0)


class PointInTimeTests(unittest.TestCase):
    ROWS = [
        {"filing_date": "2026-07-29", "revenue": 100},
        {"filing_date": "2025-07-30", "revenue": 90},
        {"filing_date": "2024-07-25", "revenue": 80},
    ]

    def test_uses_only_what_was_public(self):
        as_of = 1780000000        # mid-2026, before the July filing
        row = point_in_time(self.ROWS, as_of)
        self.assertEqual(row["revenue"], 90)

    def test_never_returns_a_future_filing(self):
        as_of = 1600000000        # 2020: nothing existed yet
        self.assertIsNone(point_in_time(self.ROWS, as_of))

    def test_returns_the_most_recent_public_one(self):
        row = point_in_time(self.ROWS, 1795000000)
        self.assertEqual(row["revenue"], 100)
