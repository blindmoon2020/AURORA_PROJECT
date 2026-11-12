import unittest

from aurora.core.types import Candle
from aurora.strategies.carry import carry_positions


def bars(n=30):
    return [Candle(ts=i * 86400, open=1.0, high=1.0, low=1.0, close=1.0) for i in range(n)]


class CarryDirectionTests(unittest.TestCase):
    """The bug of 2026-11-12 must never come back silently."""

    def test_base_yielding_more_means_long_the_pair(self):
        pos = carry_positions(bars(), base_rates={0: 8.0}, quote_rates={0: 2.0})
        self.assertEqual(set(pos), {1.0},
                         "higher base rate = long the pair, and the interest accrues on it")

    def test_lower_base_rate_means_short(self):
        pos = carry_positions(bars(), base_rates={0: 2.0}, quote_rates={0: 8.0})
        self.assertEqual(set(pos), {-1.0})

    def test_accrual_sign_matches_the_position(self):
        # carry on a long pair position is (rate(base) - rate(quote)) per day
        pos = carry_positions(bars(), base_rates={0: 8.0}, quote_rates={0: 2.0})[0]
        accrual = pos * (8.0 - 2.0) / 365.0 / 100.0
        self.assertGreater(accrual, 0.0)


if __name__ == "__main__":
    unittest.main()
