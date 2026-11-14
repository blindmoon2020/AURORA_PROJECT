import math
import unittest

from aurora.analysis import advanced_ta as ta
from aurora.core.types import Candle


def bars(prices, start=0, volume=1000.0, spread=0.01):
    out = []
    for i, p in enumerate(prices):
        out.append(Candle(ts=start + i * 86400, open=p, high=p * (1 + spread),
                          low=p * (1 - spread), close=p, volume=volume))
    return out


class SwingTests(unittest.TestCase):
    def test_swings_ignore_the_last_k_bars_so_the_verdict_cannot_change_retroactively(self):
        closes = [1, 2, 3, 2, 1, 2, 3]
        early = ta.swing_points(closes, k=2)
        self.assertFalse(any(s.index >= len(closes) - 2 for s in early))

    def test_a_clear_peak_is_found(self):
        closes = [1, 2, 5, 2, 1]
        points = ta.swing_points(closes, k=1)
        self.assertTrue(any(s.kind == "high" and s.index == 2 for s in points))

    def test_k_must_be_positive(self):
        with self.assertRaises(ValueError):
            ta.swing_points([1, 2, 3], k=0)


class StructureTests(unittest.TestCase):
    def test_rising_highs_and_lows_is_an_uptrend(self):
        closes = [1, 2, 1.5, 3, 2.5, 4, 3.5, 5]
        self.assertEqual(ta.trend_structure(ta.swing_points(closes, 1)), ta.RISE)

    def test_falling_highs_and_lows_is_a_downtrend(self):
        closes = [5, 4, 4.5, 3, 3.5, 2, 2.5, 1]
        self.assertEqual(ta.trend_structure(ta.swing_points(closes, 1)), ta.FALL)

    def test_too_few_swings_is_a_range_not_a_guess(self):
        self.assertEqual(ta.trend_structure([]), ta.RANGE)


class BreakoutTests(unittest.TestCase):
    def test_a_new_high_breaks_the_prior_range_up(self):
        closes = [10] * 60 + [11]
        self.assertEqual(ta.range_breakout(closes, 55), ta.BREAK_UP)

    def test_a_new_low_breaks_down(self):
        closes = [10] * 60 + [9]
        self.assertEqual(ta.range_breakout(closes, 55), ta.BREAK_DOWN)

    def test_a_normal_bar_stays_inside(self):
        closes = [10] * 60 + [10.0]
        self.assertEqual(ta.range_breakout(closes, 55), ta.INSIDE)

    def test_short_history_is_inside_not_an_error(self):
        self.assertEqual(ta.range_breakout([10, 11, 12], 55), ta.INSIDE)


class VolatilityTests(unittest.TestCase):
    def test_atr_is_a_price_distance(self):
        b = bars([100, 101, 102, 101, 103, 104])
        value = ta.atr([x.high for x in b], [x.low for x in b], [x.close for x in b], n=3)
        self.assertGreater(value, 0)

    def test_atr_needs_enough_bars(self):
        b = bars([100, 101])
        self.assertIsNone(ta.atr([x.high for x in b], [x.low for x in b],
                                [x.close for x in b], n=14))

    def test_atr_percent_is_relative_to_price(self):
        b = bars([100] * 30)
        self.assertIsNotNone(ta.atr_pct([x.high for x in b], [x.low for x in b],
                                        [x.close for x in b]))

    def test_mismatched_series_are_refused(self):
        with self.assertRaises(ValueError):
            ta.true_ranges([1, 2], [1], [1, 2])


class RsiTests(unittest.TestCase):
    def test_only_gains_gives_one_hundred(self):
        self.assertEqual(ta.rsi([1, 2, 3, 4, 5, 6], n=3), 100.0)

    def test_only_losses_gives_zero(self):
        self.assertAlmostEqual(ta.rsi([6, 5, 4, 3, 2, 1], n=3), 0.0)

    def test_a_flat_series_is_neutral_not_undefined(self):
        self.assertEqual(ta.rsi([5] * 10, n=5), 50.0)

    def test_short_history_returns_none(self):
        self.assertIsNone(ta.rsi([1, 2], n=14))


class VolumeProfileTests(unittest.TestCase):
    def test_the_poc_sits_where_volume_concentrated(self):
        closes = [100, 101, 102, 102, 102, 103, 104]
        volumes = [10, 10, 500, 500, 500, 10, 10]
        vp = ta.volume_profile(closes, volumes, bins=6)
        self.assertAlmostEqual(vp["poc"], 102, delta=1.5)

    def test_the_value_area_brackets_the_poc(self):
        closes = [100 + i % 5 for i in range(60)]
        volumes = [100.0] * 60
        vp = ta.volume_profile(closes, volumes, bins=10)
        low, high = vp["value_area"]
        self.assertLessEqual(low, vp["poc"])
        self.assertGreaterEqual(high, vp["poc"])

    def test_mismatched_lengths_are_refused(self):
        with self.assertRaises(ValueError):
            ta.volume_profile([1, 2, 3], [1, 2])

    def test_a_flat_price_gives_a_degenerate_profile_not_a_crash(self):
        vp = ta.volume_profile([100] * 30, [10] * 30, bins=6)
        self.assertEqual(vp["poc"], 100)


class ProfileWindowTests(unittest.TestCase):
    """Debt from AUDIT 4.16: the point of control was computed over 20 years, so the
    percentage versus today was meaningless (+3404%). This locks the window."""

    def test_the_profile_uses_a_recent_window_not_the_whole_history(self):
        older = [10 + (i % 3) for i in range(400)]        # ancient prices around 10
        recent = [100 + (i % 3) for i in range(300)]      # current prices around 100
        read = ta.technical_read("X", bars(older + recent), profile_window=252)
        self.assertGreater(read.poc, 90, "POC باید از پنجره اخیر باشد نه تاریخ باستان")
        self.assertLess(abs(read.price_vs_poc_pct), 15)

    def test_the_window_is_stated_in_the_reason(self):
        read = ta.technical_read("X", bars([100 + i * 0.1 for i in range(300)]),
                                 profile_window=252)
        self.assertTrue(any("پنجره" in r for r in read.reasons))


class ReadTests(unittest.TestCase):
    def test_a_full_read_carries_structure_breakout_and_measurements(self):
        closes = [100 + i * 0.5 for i in range(120)]
        read = ta.technical_read("AAPL", bars(closes))
        self.assertEqual(read.symbol, "AAPL")
        self.assertIn(read.structure, (ta.RISE, ta.FALL, ta.RANGE))
        self.assertIsNotNone(read.atr_pct)
        self.assertTrue(any("%" in r for r in read.reasons))

    def test_an_empty_series_says_so(self):
        read = ta.technical_read("AAPL", [])
        self.assertTrue(read.warnings)

    def test_contradictions_are_reported_not_smoothed(self):
        closes = [100] * 60 + [90]
        read = ta.technical_read("X", bars(closes))
        self.assertEqual(read.breakout, ta.BREAK_DOWN)

    def test_confirmation_never_claims_certainty(self):
        closes = [100 + i * 0.4 for i in range(120)]
        label = ta.confirmation(ta.technical_read("AAPL", bars(closes)))
        self.assertIn(label, ("هم‌جهت با روند", "هم‌جهت با روند نزولی", "بدون تأیید", "متناقض"))


if __name__ == "__main__":
    unittest.main()
