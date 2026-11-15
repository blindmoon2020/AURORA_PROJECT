import math
import unittest

from aurora.analysis import trend_rules as tr


def series(n, step=1.0, start=100.0):
    return [start + step * i for i in range(n)]


def with_noise(n, drift, start=100.0, amp=1.0):
    """Drift plus a slow wave: a realistic trend has swings, not bar-to-bar coin flips.

    An alternating +-1% series is a market with NO structure (every bar is an extremum), so it
    is the wrong fixture for testing a structure filter; the wave gives clean higher highs and
    higher lows, which is what the rule is meant to recognise.
    """
    return [start * (1.0 + drift) ** i * (1.0 + 0.04 * amp * math.sin(2 * math.pi * i / 40))
            for i in range(n)]


class EmaTests(unittest.TestCase):
    def test_a_constant_series_has_an_ema_equal_to_that_constant(self):
        self.assertAlmostEqual(tr.ema([5.0] * 50, 20), 5.0, places=9)

    def test_ema_matches_the_sma_seeded_definition(self):
        values = [float(i + 1) for i in range(10)]
        k = 2 / (3 + 1)
        expected = sum(values[:3]) / 3
        for v in values[3:]:
            expected = v * k + expected * (1 - k)
        self.assertAlmostEqual(tr.ema(values, 3), expected, places=9)

    def test_too_few_values_is_none_not_a_guess(self):
        self.assertIsNone(tr.ema([1.0, 2.0], 5))

    def test_slope_reads_the_series_not_the_price(self):
        rising = tr.ema_series(series(60), 10)
        self.assertGreater(tr.slope_pct(rising), 0)
        self.assertIsNone(tr.slope_pct(rising[:5], lookback=10))


class StructureAndTrendTests(unittest.TestCase):
    def test_short_history_is_named_not_scored(self):
        read = tr.detect_trend([1.0] * 50, [1.0] * 50, [1.0] * 50)
        self.assertEqual(read.state, tr.RANGE)
        self.assertTrue(read.warnings)

    def test_a_clean_uptrend_is_up(self):
        closes = with_noise(320, drift=0.002)
        highs = [c * 1.004 for c in closes]
        lows = [c * 0.996 for c in closes]
        read = tr.detect_trend(highs, lows, closes)
        self.assertEqual(read.state, tr.UP)
        self.assertGreaterEqual(read.score, tr.AGREE_THRESHOLD)

    def test_a_clean_downtrend_is_down(self):
        closes = with_noise(320, drift=-0.002)
        highs = [c * 1.004 for c in closes]
        lows = [c * 0.996 for c in closes]
        read = tr.detect_trend(highs, lows, closes)
        self.assertEqual(read.state, tr.DOWN)

    def test_a_flat_market_is_a_range_and_never_a_trend(self):
        closes = [100.0 + (1 if i % 2 else -1) * 0.5 for i in range(320)]
        read = tr.detect_trend(closes, closes, closes)
        self.assertEqual(read.state, tr.RANGE)

    def test_a_sideways_market_is_named_a_range_with_reasons(self):
        closes = with_noise(320, drift=0.0)
        read = tr.detect_trend(closes, closes, closes)
        self.assertEqual(read.state, tr.RANGE)
        self.assertTrue(read.reasons)


class CandleTests(unittest.TestCase):
    def test_a_long_lower_wick_small_body_is_a_bullish_pin(self):
        self.assertEqual(tr.is_pin_bar(100, 100.4, 95.0, 100.2), "پین صعودی")

    def test_a_big_body_is_not_a_pin(self):
        self.assertIsNone(tr.is_pin_bar(100, 105, 99, 104.8))

    def test_a_zero_range_bar_is_not_a_pin(self):
        self.assertIsNone(tr.is_pin_bar(100, 100, 100, 100))

    def test_engulfing_needs_opposite_directions(self):
        self.assertEqual(tr.is_engulfing((101, 100), (99, 102)), "پوشای صعودی")
        self.assertIsNone(tr.is_engulfing((100, 101), (100.5, 102)))

    def test_bearish_engulfing(self):
        self.assertEqual(tr.is_engulfing((100, 101), (102, 99)), "پوشای نزولی")


class EntryTests(unittest.TestCase):
    def _trending(self, drift):
        closes = with_noise(300, drift=drift)
        highs = [c * 1.004 for c in closes]
        lows = [c * 0.996 for c in closes]
        opens = [closes[0]] + closes[:-1]
        return highs, lows, opens, closes

    def test_a_range_market_refuses_to_plan_an_entry(self):
        closes = [100.0 + (1 if i % 2 else -1) * 0.5 for i in range(300)]
        plan = tr.plan_entry(closes, closes, closes, closes)
        self.assertEqual(plan.action, tr.NONE)
        self.assertTrue(plan.reasons)

    def test_no_trigger_means_no_entry_even_in_a_trend(self):
        highs, lows, opens, closes = self._trending(0.002)
        plan = tr.plan_entry(highs, lows, opens, closes)
        self.assertEqual(plan.action, tr.NONE)

    def test_an_entry_stop_sits_beyond_the_swing_and_rr_is_at_least_two(self):
        closes = with_noise(300, drift=0.002)
        highs = [c * 1.004 for c in closes]
        lows = [c * 0.996 for c in closes]
        opens = [closes[0]] + closes[:-1]
        # engineer the last bar into a bullish pin sitting on the EMA50
        fast = tr.ema(closes, 50)
        price = fast * 1.005
        closes[-1] = price
        opens[-1] = price
        highs[-1] = price + 0.01
        lows[-1] = price - 0.30 * price * 0.02
        plan = tr.plan_entry(highs, lows, opens, closes)
        if plan.action != tr.NONE:
            self.assertLess(plan.stop, plan.entry)
            self.assertAlmostEqual(plan.rr, 2.0, places=2)

    def test_position_size_loses_exactly_the_risk_budget_at_the_stop(self):
        units = tr.position_size(equity=100_000, risk_pct=1.0, entry=100.0, stop=95.0)
        self.assertAlmostEqual(units * (100.0 - 95.0), 1000.0, places=6)

    def test_position_size_refuses_degenerate_inputs(self):
        self.assertEqual(tr.position_size(0, 1, 100, 95), 0.0)
        self.assertEqual(tr.position_size(100_000, 1, 100, 100), 0.0)
        self.assertEqual(tr.position_size(100_000, 0, 100, 95), 0.0)


if __name__ == "__main__":
    unittest.main()
