import unittest

from aurora.core.types import Candle
from aurora.analysis import (atr, fibonacci, price_action, range_position,
                             support_resistance, swings, volume_profile)


def bar(i, o, h, l, c, v=0.0):
    return Candle(ts=1700000000 + i * 3600, open=o, high=h, low=l, close=c, volume=v)


def zigzag():
    """Up leg to 1.20, down leg through 1.10, then a bounce: known structure."""
    out, price = [], 1.10
    for i in range(40):
        price += 0.0025
        out.append(bar(i, price - 0.0005, price + 0.001, price - 0.0015, price))
    top = price
    for i in range(40, 80):
        price -= 0.0025
        out.append(bar(i, price + 0.0005, price + 0.0015, price - 0.001, price))
    bottom = price
    for i in range(80, 95):
        price += 0.0018
        out.append(bar(i, price - 0.0004, price + 0.0008, price - 0.0012, price))
    return out, top, bottom


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.candles, self.top, self.bottom = zigzag()

    def test_atr_is_positive_and_bounded(self):
        e = atr(self.candles)
        self.assertGreater(e, 0)
        self.assertLess(e, 0.01)

    def test_swings_find_the_top_and_bottom(self):
        piv = swings(self.candles, k=3)
        highs = [p for _i, p, kind in piv if kind == "high"]
        lows = [p for _i, p, kind in piv if kind == "low"]
        self.assertTrue(any(abs(p - self.top) < 0.002 for p in highs))
        self.assertTrue(any(abs(p - self.bottom) < 0.002 for p in lows))

    def test_support_resistance_are_classified_around_price(self):
        levels = support_resistance(self.candles, k=3)
        self.assertTrue(levels)
        last = self.candles[-1].close
        for lv in levels:
            self.assertEqual(lv.kind, "resistance" if lv.price > last else "support")
            self.assertGreaterEqual(lv.touches, 1)

    def test_fibonacci_retraces_the_up_leg(self):
        fib = fibonacci(self.candles, lookback=200)
        self.assertIn(fib["direction"], ("up", "down"))
        self.assertAlmostEqual(fib["levels"][0.5],
                               (fib["high"] + fib["low"]) / 2, places=9)
        # 0.618 always sits deeper into the leg than 0.5, whichever way the leg runs
        if fib["direction"] == "up":
            self.assertLess(fib["levels"][0.618], fib["levels"][0.5])
        else:
            self.assertGreater(fib["levels"][0.618], fib["levels"][0.5])

    def test_range_position_is_inside_the_range(self):
        pos = range_position(self.candles, lookback=100)
        self.assertGreaterEqual(pos, 0)
        self.assertLessEqual(pos, 1)

    def test_volume_profile_without_volume_refuses(self):
        prof = volume_profile(self.candles)
        self.assertFalse(prof["has_volume"])
        self.assertIsNone(prof["poc"])

    def test_volume_profile_finds_poc_of_dense_price(self):
        bars = [bar(i, 1.10, 1.101, 1.099, 1.10, v=100) for i in range(30)]
        bars += [bar(30 + i, 1.20, 1.201, 1.199, 1.20, v=1) for i in range(5)]
        prof = volume_profile(bars, bins=12)
        self.assertTrue(prof["has_volume"])
        self.assertAlmostEqual(prof["poc"], 1.10, delta=0.01)
        lo, hi = prof["value_area"]
        self.assertLess(lo, prof["poc"])
        self.assertGreater(hi, prof["poc"])

    def test_engulfing_and_break_of_structure(self):
        bars = [bar(i, 1.10, 1.101, 1.099, 1.10) for i in range(20)]
        bars.append(bar(20, 1.10, 1.1005, 1.0980, 1.0985))
        bars.append(bar(21, 1.0982, 1.1040, 1.0980, 1.1035))
        names = [p.name for p in price_action(bars)]
        self.assertIn("bullish_engulfing", names)
        self.assertIn("bos_up", names)

    def test_short_series_is_safe(self):
        self.assertEqual(swings([bar(0, 1, 1, 1, 1)]), [])
        self.assertEqual(price_action([bar(0, 1, 1, 1, 1)]), [])
        self.assertEqual(fibonacci([bar(0, 1, 1, 1, 1)]), {})


if __name__ == "__main__":
    unittest.main()
