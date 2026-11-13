import unittest

from aurora.execution.tca import Fill, analyse, slippage_bps
from aurora.risk.analysis import capacity, factor_exposure


class TCATests(unittest.TestCase):
    def test_buy_paying_more_is_positive_slippage(self):
        self.assertGreater(slippage_bps(Fill("A", "BUY", 1, 100.0, 100.5)), 0)

    def test_sell_receiving_less_is_positive_slippage(self):
        self.assertGreater(slippage_bps(Fill("A", "SELL", 1, 100.0, 99.5)), 0)

    def test_sell_receiving_more_is_negative(self):
        self.assertLess(slippage_bps(Fill("A", "SELL", 1, 100.0, 100.5)), 0)

    def test_zero_ticket_price_is_refused(self):
        with self.assertRaises(ValueError):
            slippage_bps(Fill("A", "BUY", 1, 0.0, 100.0))

    def test_clean_execution_passes_the_verdict(self):
        rep = analyse([Fill("A", "BUY", 10, 100.0, 100.01)])
        self.assertIn("in line", rep.verdict)

    def test_poor_execution_is_called_out(self):
        rep = analyse([Fill("A", "BUY", 10, 100.0, 100.5)])
        self.assertIn("recalibrate", rep.verdict)

    def test_empty_book(self):
        self.assertEqual(analyse([]).fills, 0)


class CapacityTests(unittest.TestCase):
    def test_capacity_is_participation_times_adtv(self):
        c = capacity(100.0, 1_000_000, participation=0.01)
        self.assertAlmostEqual(c.max_position_usd, 1_000_000.0)

    def test_bad_participation_is_refused(self):
        with self.assertRaises(ValueError):
            capacity(100.0, 1000, participation=0.0)
        with self.assertRaises(ValueError):
            capacity(100.0, 1000, participation=2.0)

    def test_reason_states_the_verdict(self):
        c = capacity(10.0, 1000, participation=0.01)
        self.assertIn("ABOVE capacity", c.reason)


class ExposureTests(unittest.TestCase):
    def test_pure_market_beta_is_one(self):
        # a constant series has zero variance, so R2 is undefined and float
        # summation order decides the answer: use a series that actually varies
        market = [0.01, -0.01] * 30
        e = factor_exposure(market, market)
        self.assertAlmostEqual(e.market, 1.0, places=6)
        self.assertAlmostEqual(e.r_squared, 1.0, places=6)
        self.assertLess(e.residual_vol, 1e-9)

    def test_zero_beta_book_is_detected(self):
        e = factor_exposure([0.0] * 60, [0.01, -0.01] * 30)
        self.assertAlmostEqual(e.market, 0.0, places=6)

    def test_short_history_is_refused(self):
        with self.assertRaises(ValueError):
            factor_exposure([0.01] * 10, [0.01] * 10)


if __name__ == "__main__":
    unittest.main()
