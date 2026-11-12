import math
import unittest

from aurora.risk.portfolio import (CorrelationMatrix, PortfolioLimits, PortfolioRisk,
                                   correlation)


class CorrelationTests(unittest.TestCase):
    def test_perfect_and_inverse(self):
        a = [0.01, -0.02, 0.03, 0.005, -0.001]
        self.assertAlmostEqual(correlation(a, a), 1.0, places=6)
        self.assertAlmostEqual(correlation(a, [-x for x in a]), -1.0, places=6)

    def test_undefined_is_none_not_zero(self):
        self.assertIsNone(correlation([0.01], [0.02]))
        self.assertIsNone(correlation([0.01] * 5, [0.02] * 5))

    def test_matrix_is_symmetric_with_unit_diagonal(self):
        cm = CorrelationMatrix.from_returns(
            {"A": [0.01, -0.01, 0.02, 0.0], "B": [0.011, -0.009, 0.019, 0.001]},
            class_of=lambda s: "fx")
        self.assertEqual(cm.get("A", "A"), 1.0)
        self.assertAlmostEqual(cm.get("A", "B"), cm.get("B", "A"), places=12)
        self.assertGreater(cm.get("A", "B"), 0.9)


class PortfolioRiskTests(unittest.TestCase):
    def setUp(self):
        cm = CorrelationMatrix(values={("EURUSD", "GBPUSD"): 0.85}, class_of=lambda s: "fx")
        self.pr = PortfolioRisk(PortfolioLimits(max_portfolio_risk_pct=1.5,
                                                max_class_risk_pct=1.0), cm)

    def test_first_position_is_size_of_its_risk(self):
        d = self.pr.evaluate("EURUSD", "fx", 50, 10_000)
        self.assertTrue(d.approved)
        self.assertAlmostEqual(d.effective_risk_money, 50.0, places=9)

    def test_correlation_makes_two_positions_cheaper_than_two(self):
        self.pr.add("EURUSD", "fx", 50)
        d = self.pr.evaluate("GBPUSD", "fx", 50, 10_000)
        self.assertAlmostEqual(d.effective_risk_money,
                               math.sqrt(50**2 + 50**2 + 2 * 50 * 50 * 0.85), places=6)

    def test_class_cap_rejects_the_fourth_correlated_position(self):
        for sym in ("EURUSD", "GBPUSD", "AUDUSD"):
            self.pr.add(sym, "fx", 50)
        d = self.pr.evaluate("NZDUSD", "fx", 50, 10_000)
        self.assertFalse(d.approved)
        self.assertFalse(d.approved)

    def test_uncorrelated_class_has_its_own_budget(self):
        self.pr.add("EURUSD", "fx", 50)
        d = self.pr.evaluate("GC=F", "metal", 50, 10_000)
        self.assertTrue(d.approved)
        self.assertAlmostEqual(d.class_risk_after_pct, 0.5, places=6)

    def test_stops_are_capped(self):
        self.pr.add("EURUSD", "fx", 50)
        self.pr.add("GBPUSD", "fx", 50)
        d = self.pr.evaluate("AUDUSD", "fx", 50, 10_000)
        self.assertFalse(d.approved)


if __name__ == "__main__":
    unittest.main()
