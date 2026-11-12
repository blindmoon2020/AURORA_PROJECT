import math
import unittest

from aurora.core.types import Candle
from aurora.strategies.tsmom import backtest_tsmom, combine


def series(prices):
    out = []
    for i, px in enumerate(prices):
        out.append(Candle(ts=i * 86_400, open=px, high=px * 1.002,
                          low=px * 0.998, close=px, volume=0.0))
    return out


class MomentumTests(unittest.TestCase):
    def test_a_rising_market_is_held_long_and_earns(self):
        prices = [100 * (1.0006 ** i) for i in range(600)]
        res = backtest_tsmom(series(prices), "UP", cost_rate=0.0)
        self.assertGreater(res.total_return_pct, 10.0)
        self.assertGreater(res.avg_abs_exposure, 0.5)

    def test_a_falling_market_is_held_short_and_earns(self):
        prices = [100 * (0.9994 ** i) for i in range(600)]
        res = backtest_tsmom(series(prices), "DOWN", cost_rate=0.0)
        self.assertGreater(res.total_return_pct, 5.0)
        self.assertGreater(res.avg_abs_exposure, 0.5)

    def test_costs_reduce_the_result_and_never_improve_it(self):
        prices = [100 + 8 * math.sin(i / 9.0) + i * 0.02 for i in range(900)]
        cheap = backtest_tsmom(series(prices), "CHOP", cost_rate=0.0)
        dear = backtest_tsmom(series(prices), "CHOP", cost_rate=0.01)
        self.assertGreater(cheap.total_return_pct, dear.total_return_pct)
        self.assertEqual(cheap.flips, dear.flips)

    def test_not_enough_history_is_refused_not_faked(self):
        with self.assertRaises(ValueError):
            backtest_tsmom(series([100.0] * 50), "SHORT")

    def test_combination_is_equal_weight_and_truncates_to_the_shortest(self):
        a = [0.01] * 10
        b = [0.02] * 20
        out = combine({"a": a, "b": b})
        self.assertEqual(len(out), 10)
        self.assertAlmostEqual(out[0], 0.015, places=12)


if __name__ == "__main__":
    unittest.main()
