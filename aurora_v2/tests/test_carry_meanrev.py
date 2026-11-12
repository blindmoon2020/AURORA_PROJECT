import unittest

from aurora.core.types import Candle
from aurora.strategies.carry import carry_positions, rate_at
from aurora.strategies.meanrev import zscore_positions


def flat(n, price=1.0, step_hours=86400):
    return [Candle(ts=i * step_hours, open=price, high=price, low=price, close=price)
            for i in range(n)]


class RateLookupTests(unittest.TestCase):
    def test_never_uses_a_rate_from_the_future(self):
        self.assertIsNone(rate_at(100, {200: 5.0}))

    def test_uses_the_latest_known_rate(self):
        self.assertEqual(rate_at(250, {100: 1.0, 200: 2.0, 300: 3.0}), 2.0)


class CarryTests(unittest.TestCase):
    def test_long_the_higher_yielder(self):
        pos = carry_positions(flat(30), {0: 6.0}, {0: 1.0})
        self.assertEqual(set(pos), {1.0})

    def test_short_the_pair_when_the_base_pays_less(self):
        pos = carry_positions(flat(30), {0: 1.0}, {0: 6.0})
        self.assertEqual(set(pos), {-1.0})

    def test_stand_aside_when_no_rate_is_published_yet(self):
        self.assertEqual(set(carry_positions(flat(10), {}, {})), {0.0})

    def test_rebalance_holds_the_position_between_dates(self):
        candles = flat(45)
        rates_a = {0: 5.0, 21 * 86400: 1.0}     # yield ranking flips at the second rebalance
        rates_b = {0: 1.0, 21 * 86400: 5.0}
        pos = carry_positions(candles, rates_a, rates_b, rebalance_days=21)
        self.assertEqual(pos[5], 1.0)
        self.assertEqual(pos[25], -1.0)


class MeanReversionTests(unittest.TestCase):
    def test_fades_a_sharp_rally(self):
        prices = [1.0] * 200 + [1.0 * (1.01 ** i) for i in range(1, 30)]
        candles = [Candle(ts=i * 3600, open=p, high=p, low=p, close=p) for i, p in enumerate(prices)]
        pos = zscore_positions(candles)
        self.assertTrue(any(p < 0 for p in pos), "a vertical rally must invite a short fade")

    def test_time_stop_closes_the_trade(self):
        prices = [1.0] * 200 + [1.0 * (1.01 ** i) for i in range(1, 40)]
        candles = [Candle(ts=i * 3600, open=p, high=p, low=p, close=p) for i, p in enumerate(prices)]
        pos = zscore_positions(candles, max_hold=3)
        run = max((len(list(g)) for k, g in __import__("itertools").groupby(pos) if k != 0.0), default=0)
        self.assertLessEqual(run, 3)

    def test_quiet_market_produces_no_position(self):
        pos = zscore_positions(flat(300))
        self.assertEqual(set(pos), {0.0})


if __name__ == "__main__":
    unittest.main()
