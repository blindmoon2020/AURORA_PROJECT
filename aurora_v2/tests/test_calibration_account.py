import os
import unittest

from aurora.calibration import calibrate, measure, slippage_bps
from aurora.vault import account_total, from_minor, money, protect_account

KEY = "calibration-test-key"


class SlippageTests(unittest.TestCase):
    def test_buy_above_decision_is_positive(self):
        self.assertAlmostEqual(slippage_bps(100.0, 100.1, is_buy=True), 10.0, places=6)

    def test_sell_below_decision_is_also_worse(self):
        self.assertAlmostEqual(slippage_bps(100.0, 99.9, is_buy=False), 10.0, places=6)

    def test_better_than_decision_is_negative(self):
        self.assertLess(slippage_bps(100.0, 99.95, is_buy=True), 0)

    def test_bad_price_is_refused(self):
        with self.assertRaises(ValueError):
            slippage_bps(0.0, 100.0)


class CalibrationTests(unittest.TestCase):
    def test_no_fills_keeps_the_assumption_and_says_uncalibrated(self):
        c = calibrate([], assumption_bps=10.0)
        self.assertFalse(c.confident)
        self.assertEqual(c.calibrated_bps, 10.0)
        self.assertIn("uncalibrated", c.summary())

    def test_too_few_fills_does_not_overwrite_the_assumption(self):
        c = calibrate([50.0] * 5, assumption_bps=10.0)
        self.assertFalse(c.confident)
        self.assertGreaterEqual(c.calibrated_bps, 10.0)   # worse cost raises it, never lowers

    def test_many_consistent_fills_calibrate(self):
        c = calibrate([25.0] * 40, assumption_bps=10.0)
        self.assertTrue(c.confident)
        self.assertLess(c.calibrated_bps, 25.0)           # shrunk toward the prior
        self.assertGreater(c.calibrated_bps, 10.0)

    def test_noise_around_the_assumption_stays_unconfirmed(self):
        obs = [0.0, 20.0] * 20          # mean 10.0: exactly the assumption, wide spread
        c = calibrate(obs, assumption_bps=10.0)
        self.assertFalse(c.confident)

    def test_a_clear_shift_outranks_noise(self):
        obs = [10.0, 60.0] * 20         # mean 35 vs assumption 10: real difference
        self.assertTrue(calibrate(obs, assumption_bps=10.0).confident)

    def test_measure_reads_triples(self):
        self.assertAlmostEqual(measure([(100.0, 100.1, True)])[0], 10.0, places=6)


class AccountVaultTests(unittest.TestCase):
    def setUp(self):
        os.environ["AURORA_PSEUDONYM_KEY"] = KEY

    def tearDown(self):
        os.environ.pop("AURORA_PSEUDONYM_KEY", None)

    def test_money_is_integer_minor_units(self):
        safe = protect_account({"cash_balance": 1250.75})
        self.assertEqual(safe["cash_balance_minor"], 125075)
        self.assertEqual(from_minor(125075), 1250.75)
        self.assertNotIn("cash_balance", safe)

    def test_float_addition_problem_is_absent(self):
        self.assertEqual(money(0.1) + money(0.2), money(0.3))

    def test_fees_are_separate_from_net(self):
        row = protect_account({"proceeds": 1000.0, "fee": 4.5, "cash_balance": 995.5})
        self.assertEqual(row["net_minor"], money(995.5))
        self.assertAlmostEqual(row["cost_share_pct"], 0.45, places=4)

    def test_identity_is_pseudonymised(self):
        row = protect_account({"customer_id": "c-99", "cash_balance": 10.0})
        self.assertNotEqual(row["customer_id"], "c-99")

    def test_totals_stay_integer(self):
        rows = [protect_account({"cash_balance": 10.05}),
                protect_account({"cash_balance": 20.10})]
        self.assertEqual(account_total(rows), money(30.15))


if __name__ == "__main__":
    unittest.main()
