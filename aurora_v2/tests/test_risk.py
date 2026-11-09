import unittest

from aurora.core.types import Side
from aurora.risk import RiskEngine, RiskLimits


class RiskSizingTests(unittest.TestCase):
    def setUp(self):
        self.risk = RiskEngine(RiskLimits(risk_per_trade_pct=1.0, daily_loss_cap_pct=2.0,
                                          max_open_positions=1, max_leverage=30.0))
        self.risk.start_day(10_000.0)

    def test_sizes_from_account_risk(self):
        d = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.1000,
                               stop=1.0950, equity=10_000.0)
        self.assertTrue(d.approved, d.reason)
        self.assertAlmostEqual(d.risk_money, 100.0, places=2)
        # 100 risk / 0.0050 stop distance = 20,000 units
        self.assertAlmostEqual(d.units, 20_000.0, places=4)

    def test_stop_on_wrong_side_is_rejected(self):
        d = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.1000,
                               stop=1.1100, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("invalid stop", d.reason)

    def test_zero_distance_is_rejected(self):
        d = self.risk.evaluate(symbol="EURUSD", side=Side.SHORT, entry=1.1,
                               stop=1.1, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("invalid stop", d.reason)

    def test_exposure_ceiling_blocks_absurd_units(self):
        d = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.1000,
                               stop=1.0999, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("exposure ceiling", d.reason)

    def test_one_position_per_symbol(self):
        self.risk.register_open("EURUSD", 20_000.0)
        d = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.1,
                               stop=1.095, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("max open positions", d.reason)

    def test_max_open_positions(self):
        self.risk.register_open("EURUSD", 20_000.0)
        d = self.risk.evaluate(symbol="XAUUSD", side=Side.LONG, entry=2000.0,
                               stop=1990.0, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("max open positions", d.reason)


class RiskGuardrailTests(unittest.TestCase):
    def setUp(self):
        self.risk = RiskEngine(RiskLimits(risk_per_trade_pct=0.5, daily_loss_cap_pct=2.0))
        self.risk.start_day(10_000.0)

    def test_daily_loss_cap_stops_trading(self):
        self.risk.register_open("EURUSD", 20_000.0)
        self.risk.register_close("EURUSD", -250.0)
        self.assertAlmostEqual(self.risk.daily_loss_pct, 2.5)
        d = self.risk.evaluate(symbol="EURUSD", side=Side.SHORT, entry=1.10,
                               stop=1.105, equity=9_750.0)
        self.assertFalse(d.approved)
        self.assertIn("daily loss cap", d.reason)

    def test_new_day_resets_the_cap(self):
        self.risk.register_open("EURUSD", 20_000.0)
        self.risk.register_close("EURUSD", -250.0)
        self.risk.start_day(9_750.0)
        self.assertEqual(self.risk.daily_loss_pct, 0.0)
        self.assertFalse(self.risk.daily_cap_hit())

    def test_kill_switch_blocks_everything_until_reset(self):
        self.risk.trip("manual: spread blowout")
        d = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.10,
                               stop=1.095, equity=10_000.0)
        self.assertFalse(d.approved)
        self.assertIn("kill switch", d.reason)
        self.risk.reset()
        d2 = self.risk.evaluate(symbol="EURUSD", side=Side.LONG, entry=1.10,
                                stop=1.095, equity=10_000.0)
        self.assertTrue(d2.approved, d2.reason)

    def test_limits_are_validated(self):
        with self.assertRaises(ValueError):
            RiskLimits(risk_per_trade_pct=0).validate()
        with self.assertRaises(ValueError):
            RiskLimits(daily_loss_cap_pct=99).validate()


if __name__ == "__main__":
    unittest.main()
