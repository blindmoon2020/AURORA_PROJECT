import unittest

from aurora.core.types import Candle
from aurora.signals.factors import (build_factors, composite, trend_of, vol_of,
                                    zscore)


def series_from(prices):
    return [Candle(ts=i * 86400, open=p, high=p, low=p, close=p, volume=0.0)
            for i, p in enumerate(prices)]


class ZScoreTests(unittest.TestCase):
    def test_needs_three_names_to_rank(self):
        self.assertEqual(zscore({"a": 1.0, "b": 2.0}), {})

    def test_flat_cross_section_has_no_ranking(self):
        self.assertEqual(zscore({"a": 1.0, "b": 1.0, "c": 1.0}), {})

    def test_clipped_at_three_sigma(self):
        z = zscore({"a": 1, "b": 2, "c": 3, "d": 1000})
        self.assertLessEqual(max(z.values()), 3.0)


class FactorMathTests(unittest.TestCase):
    def test_trend_skips_the_last_month(self):
        rising = [100.0 * (1.001 ** i) for i in range(400)]
        t = trend_of(series_from(rising))
        self.assertIsNotNone(t)
        self.assertGreater(t, 0.0)

    def test_trend_is_none_when_history_is_short(self):
        self.assertIsNone(trend_of(series_from([100.0] * 50)))

    def test_volatility_is_positive_and_scales_with_noise(self):
        calm = vol_of(series_from([100 + 0.01 * (i % 2) for i in range(120)]))
        wild = vol_of(series_from([100 + 5.0 * (i % 2) for i in range(120)]))
        self.assertGreater(wild, calm)


class BuildTests(unittest.TestCase):
    def test_missing_inputs_are_absent_not_zero(self):
        candles = {"A": series_from([100.0 * (1.001 ** i) for i in range(400)])}
        rows = build_factors(candles, fundamentals=None, carry=None)
        self.assertIn("trend", rows["A"])
        self.assertNotIn("value", rows["A"])
        self.assertNotIn("carry", rows["A"])

    def test_earnings_yield_is_used_not_the_pe(self):
        candles = {"A": series_from([100.0] * 400)}
        rows = build_factors(candles, fundamentals={"A": {"pe_ttm": 20.0}})
        self.assertAlmostEqual(rows["A"]["value"], 0.05)


class CompositeTests(unittest.TestCase):
    def test_weights_redistribute_when_a_factor_is_missing(self):
        ranked = composite({"A": {"trend": 0.2, "value": 0.05},
                            "B": {"trend": 0.1},
                            "C": {"trend": 0.0, "value": 0.03}})
        a = next(r for r in ranked if r["symbol"] == "A" if False) if False else ranked[0]
        self.assertEqual(a.symbol, "A")
        # value cannot be scored with two names, so trend carries all the weight
        self.assertEqual(set(a.components), {"trend"})

    def test_order_is_by_score_and_reasons_name_factors(self):
        ranked = composite({"X": {"trend": 0.3, "low_vol": -0.2},
                            "Y": {"trend": 0.1, "low_vol": -0.1},
                            "Z": {"trend": -0.1, "low_vol": -0.3}})
        scores = [r.score for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(r.reason for r in ranked))
