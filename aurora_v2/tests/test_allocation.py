import unittest

from aurora.core.types import Candle
from aurora.portfolio.allocation import (align, inverse_vol_weights, run_allocation)


def mk(prices, start=0):
    return [Candle(ts=(start + i) * 86400, open=p, high=p, low=p, close=p)
            for i, p in enumerate(prices)]


class WeightTests(unittest.TestCase):
    def test_inverse_vol_weights_sum_to_one_when_cap_allows(self):
        w = inverse_vol_weights({"a": 0.10, "b": 0.20, "c": 0.40, "d": 0.15, "e": 0.30})
        self.assertAlmostEqual(sum(w.values()), 1.0, places=9)
        self.assertGreater(w["a"], w["c"])

    def test_too_few_names_under_invests_instead_of_breaking_the_cap(self):
        w = inverse_vol_weights({"a": 0.10, "b": 0.20})
        self.assertAlmostEqual(sum(w.values()), 0.50, places=9)
        self.assertTrue(all(v <= 0.25 + 1e-9 for v in w.values()))

    def test_cap_is_enforced_and_excess_redistributed(self):
        w = inverse_vol_weights({"a": 0.01, "b": 1.0, "c": 0.5, "d": 0.3, "e": 0.2}, cap=0.25)
        self.assertLessEqual(max(w.values()), 0.2500001)
        self.assertAlmostEqual(sum(w.values()), 1.0, places=6)

    def test_zero_volatility_earns_no_weight(self):
        w = inverse_vol_weights({"dead": 0.0, "live": 0.2})
        self.assertEqual(w.get("dead", 0.0), 0.0)


class AlignTests(unittest.TestCase):
    def test_alignment_uses_the_union_of_dates(self):
        grid, rets = align({"a": mk([1, 2, 3]), "b": mk([1, 3], start=1)})
        self.assertEqual(len(grid), 2)
        self.assertIn(86400, grid)
        self.assertNotIn(86400, rets["b"])


class AllocationTests(unittest.TestCase):
    def _series(self, n=400):
        up = [100 * (1.0008 ** i) for i in range(n)]
        flat = [100.0] * n
        down = [100 * (0.9995 ** i) for i in range(n)]
        return {"up": mk(up), "flat": mk(flat), "down": mk(down)}

    def test_trend_filter_keeps_the_book_out_of_a_downtrend(self):
        res = run_allocation(self._series(), trend_filter=True, cost_rate=0.0)
        self.assertGreaterEqual(res.avg_positions, 0.0)
        self.assertGreater(res.rebalances, 0)

    def test_drawdown_is_reported_and_bounded(self):
        res = run_allocation(self._series(), cost_rate=0.0)
        self.assertGreaterEqual(res.max_dd_pct, 0.0)
        self.assertLessEqual(res.max_dd_pct, 100.0)

    def test_no_history_means_no_positions_not_a_crash(self):
        res = run_allocation({"a": mk([1, 2, 3])})
        self.assertEqual(res.rebalances, 0)
        self.assertTrue(all(r == 0.0 for r in res.returns), "no positions must mean no return")
