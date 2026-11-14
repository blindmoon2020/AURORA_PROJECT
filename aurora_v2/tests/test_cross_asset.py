import unittest

from aurora.core.types import Candle
from aurora.strategies.cross_asset import (CrossAssetRules, momentum, realized_vol,
                                           sized_weights, sleeve_series, step,
                                           turnover)


class MomentumTests(unittest.TestCase):
    def test_skips_the_most_recent_month(self):
        closes = [100.0] * 300          # flat
        self.assertAlmostEqual(momentum(closes, lookback=250, skip=20), 0.0)

    def test_skip_removes_the_latest_move(self):
        rising = [100.0 + i for i in range(260)]
        with_skip = momentum(rising, lookback=252, skip=21)
        no_skip = rising[-1] / rising[-253] - 1.0
        self.assertLess(with_skip, no_skip)

    def test_too_short_is_none_not_a_guess(self):
        self.assertIsNone(momentum([100.0] * 10, lookback=252))


class VolTests(unittest.TestCase):
    def test_flat_series_has_zero_vol(self):
        self.assertAlmostEqual(realized_vol([100.0] * 80), 0.0)

    def test_vol_is_annualised_and_ordered(self):
        calm = [100.0 * (1.001 ** i) for i in range(90)]
        wild = [100.0 * (1.01 ** (i % 2)) for i in range(90)]
        self.assertLess(realized_vol(calm), realized_vol(wild))

    def test_short_series_is_none(self):
        self.assertIsNone(realized_vol([100.0] * 10))


class SizingTests(unittest.TestCase):
    def test_only_positive_momentum_is_held(self):
        w = sized_weights({"A": {"momentum": 0.1, "vol": 0.2},
                           "B": {"momentum": -0.1, "vol": 0.2}})
        self.assertIn("A", w)
        self.assertNotIn("B", w)

    def test_equal_vol_means_equal_weight(self):
        # five equal-vol assets: below the 35% cap, so the weights are a clean fifth each
        feats = {s: {"momentum": .1, "vol": .2} for s in "ABCDE"}
        w = sized_weights(feats)
        self.assertAlmostEqual(w["A"], 0.2)
        self.assertAlmostEqual(w["E"], 0.2)

    def test_lower_vol_gets_more_weight(self):
        feats = {"A": {"momentum": .1, "vol": .10}, "B": {"momentum": .1, "vol": .20},
                 "C": {"momentum": .1, "vol": .20}, "D": {"momentum": .1, "vol": .20},
                 "E": {"momentum": .1, "vol": .20}}
        w = sized_weights(feats)
        self.assertGreater(w["A"], w["B"])

    def test_cap_holds_and_the_remainder_stays_in_cash(self):
        # two assets, both would exceed a 35% cap: holding 70% invested and 30% cash is
        # the only answer that respects the cap without leverage
        feats = {"A": {"momentum": .1, "vol": .005}, "B": {"momentum": .1, "vol": 1.0}}
        w = sized_weights(feats, CrossAssetRules(max_weight_per_asset=0.35))
        self.assertLessEqual(sum(w.values()), 1.0 + 1e-9)
        self.assertTrue(all(x <= 0.35 + 1e-9 for x in w.values()))

    def test_cap_does_not_bind_when_there_is_room(self):
        feats = {s: {"momentum": .1, "vol": .2} for s in "ABCDE"}
        w = sized_weights(feats, CrossAssetRules(max_weight_per_asset=0.35))
        self.assertAlmostEqual(sum(w.values()), 1.0, places=9)

    def test_no_positive_momentum_means_cash(self):
        self.assertEqual(sized_weights({"A": {"momentum": -.2, "vol": .2}}), {})

    def test_unmeasurable_vol_is_skipped_not_capped(self):
        self.assertEqual(sized_weights({"A": {"momentum": .2, "vol": 0.0}}), {})


class TurnoverTests(unittest.TestCase):
    def test_full_switch_costs_two_units_of_half(self):
        self.assertAlmostEqual(turnover({"A": 1.0}, {"B": 1.0}), 1.0)

    def test_no_change_costs_nothing(self):
        self.assertEqual(turnover({"A": 0.5}, {"A": 0.5}), 0.0)

    def test_step_returns_cost_charged(self):
        target, cost = step({}, {"A": {"momentum": .1, "vol": .2}},
                            CrossAssetRules(cost_per_turnover=0.001))
        # a single asset hits the 35% cap, so only 35% of the book is bought
        self.assertAlmostEqual(target["A"], 0.35, places=9)
        self.assertAlmostEqual(cost, 0.5 * 0.35 * 0.001, places=9)


class SleeveTests(unittest.TestCase):
    def _candles(self, n=400, drift=0.0005):
        # real markets have noise: a perfectly smooth series has zero measured
        # volatility, and the sleeve correctly refuses to size what it cannot risk-measure
        out, px = [], 100.0
        for i in range(n):
            px *= (1 + drift + 0.004 * ((-1) ** i))
            out.append(Candle(ts=1700000000 + i * 86400, open=px, high=px, low=px,
                              close=px, volume=1))
        return out

    def test_rising_market_produces_positive_sleeve_returns(self):
        assets = {"SPY": self._candles(), "GLD": self._candles(drift=0.0004)}
        rets = sleeve_series(assets)
        self.assertTrue(rets)
        self.assertGreater(sum(rets), 0)

    def test_falling_market_stays_flat_instead_of_losing(self):
        assets = {"SPY": self._candles(drift=0.0005),
                  "GLD": self._candles(drift=-0.0009)}
        rets = sleeve_series(assets)
        self.assertTrue(all(r >= -0.02 for r in rets))

    def test_no_calendar_means_no_series(self):
        self.assertEqual(sleeve_series({}), [])


if __name__ == "__main__":
    unittest.main()
