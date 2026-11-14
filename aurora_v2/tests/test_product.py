import unittest

from aurora.core.types import Candle
from aurora.portfolio.product import (adv_notional, build_report, daily_vol_bps, markdown,
                                      screen_orders)


def candles(n=120, price=100.0, vol=1_000_000, drift=0.0004):
    out, px = [], price
    for i in range(n):
        px *= (1 + drift + 0.004 * ((-1) ** i))
        out.append(Candle(ts=1_700_000_000 + i * 86400, open=px, high=px, low=px,
                          close=px, volume=vol))
    return out


class AdvTests(unittest.TestCase):
    def test_adv_is_average_traded_value(self):
        cs = candles(vol=1000, price=100.0)
        expected = sum(c.close * c.volume for c in cs[-20:]) / 20
        self.assertAlmostEqual(adv_notional(cs, window=20), expected, places=6)

    def test_missing_volume_is_none_not_zero(self):
        cs = candles()
        bare = [Candle(c.ts, c.open, c.high, c.low, c.close, 0) for c in cs]
        self.assertIsNone(adv_notional(bare))

    def test_short_history_has_no_vol_estimate(self):
        self.assertIsNone(daily_vol_bps([100.0] * 10))

    def test_vol_is_in_basis_points(self):
        self.assertGreater(daily_vol_bps([c.close for c in candles()]), 10)


class ScreenTests(unittest.TestCase):
    def test_a_small_order_passes_and_carries_a_cost(self):
        orders = screen_orders({"AAPL": 0.10}, {"AAPL": 100.0}, 100_000,
                               {"AAPL": candles(vol=5_000_000)})
        self.assertTrue(orders[0].allowed)
        self.assertIsNotNone(orders[0].total_bps)

    def test_an_order_bigger_than_the_cap_is_refused(self):
        orders = screen_orders({"TINY": 0.90}, {"TINY": 100.0}, 100_000,
                               {"TINY": candles(vol=1000)})
        self.assertFalse(orders[0].allowed)
        self.assertIn("cap", orders[0].reason)

    def test_unknown_volume_is_unpriced_never_free(self):
        orders = screen_orders({"X": 0.1}, {"X": 50.0}, 100_000, {})
        self.assertIsNone(orders[0].total_bps)
        self.assertIn("UNPRICED", orders[0].reason)

    def test_no_price_is_refused(self):
        orders = screen_orders({"GHOST": 0.1}, {}, 100_000, {})
        self.assertFalse(orders[0].allowed)
        self.assertIn("no price", orders[0].reason)


class ReportTests(unittest.TestCase):
    def _report(self, sleeve_returns):
        orders = screen_orders({"AAPL": 0.1}, {"AAPL": 100.0}, 100_000,
                               {"AAPL": candles(vol=5_000_000)})
        return build_report({"AAPL": 0.1}, {"GLD": 0.2}, orders, sleeve_returns, [],
                            {"AAPL": 100.0, "GLD": 200.0}, 100_000,
                            {"AAPL": candles(vol=5_000_000),
                             "GLD": candles(vol=2_000_000, price=200.0)})

    def test_stress_numbers_are_filled_when_returns_exist(self):
        rep = self._report([0.01, -0.02, 0.015, -0.008] * 40)
        self.assertIsNotNone(rep.sleeve_dd_p95)
        self.assertIsNotNone(rep.crisis_loss_pct)

    def test_crisis_loss_equals_exposed_weight_times_the_shock(self):
        # 10% equity + 20% sleeve, every position down 20% together = -6% of capital
        rep = self._report([0.01, -0.02] * 60)
        self.assertLess(rep.crisis_loss_pct, 0)
        self.assertAlmostEqual(rep.crisis_loss_pct, -6.0, places=6)

    def test_missing_returns_do_not_invent_a_drawdown(self):
        rep = self._report([])
        self.assertIsNone(rep.sleeve_dd_p95)

    def test_markdown_states_what_it_cannot_claim(self):
        text = markdown(self._report([0.01, -0.01] * 60), "uncalibrated: 0 fills")
        self.assertIn("هیچ ادعای بازدهی", text)
        self.assertIn("کالیبراسیون", text)


if __name__ == "__main__":
    unittest.main()
