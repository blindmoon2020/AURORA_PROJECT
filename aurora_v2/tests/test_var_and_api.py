import unittest

from aurora.advice import onboarding as ob
from aurora.risk import portfolio_risk as pr
from aurora.web import api


def answers(level: int = 3) -> dict:
    """Same answer index for every question: a quick way to build a profile of a given stripe."""
    return {q["id"]: level for q in ob.QUESTIONS}


class VarTests(unittest.TestCase):
    def test_identical_series_correlate_exactly_one(self):
        r = {"A": [0.01, -0.02, 0.03, 0.0, 0.01], "B": [0.01, -0.02, 0.03, 0.0, 0.01]}
        m = pr.correlation_matrix(r)
        self.assertEqual(m["A"]["B"], 1.0)

    def test_opposite_series_correlate_minus_one(self):
        r = {"A": [0.01, -0.02, 0.03], "B": [-0.01, 0.02, -0.03]}
        self.assertAlmostEqual(pr.correlation_matrix(r)["A"]["B"], -1.0, places=9)

    def test_var_is_a_positive_loss_at_the_requested_tail(self):
        # 20 returns: the worst is -10%, so 95% VaR must be at least that
        series = [0.01] * 19 + [-0.10]
        self.assertAlmostEqual(pr.historical_var({"A": series}, {"A": 1.0}, 0.95), 0.10, places=9)

    def test_var_falls_when_two_uncorrelated_positions_are_combined(self):
        a = [0.02, -0.02] * 25
        b = [-0.02, 0.02] * 25
        one = pr.historical_var({"A": a}, {"A": 1.0}, 0.95)
        both = pr.historical_var({"A": a, "B": b}, {"A": 0.5, "B": 0.5}, 0.95)
        self.assertLess(both, one)

    def test_diversification_ratio_is_one_for_one_asset(self):
        r = {"A": [0.01, -0.01, 0.02, -0.02]}
        self.assertAlmostEqual(pr.diversification_ratio(r, {"A": 1.0}), 1.0, places=9)

    def test_var_without_shared_symbols_is_an_error_not_a_zero(self):
        with self.assertRaises(ValueError):
            pr.historical_var({"A": [0.01, 0.02]}, {"Z": 1.0})

    def test_the_monitor_refuses_on_position_count(self):
        mon = pr.PortfolioRiskMonitor(max_open_positions=2)
        pos = [pr.OpenPosition("A", 1, 100, 100), pr.OpenPosition("B", 1, 100, 100)]
        verdict = mon.evaluate_portfolio_risk(pos, 100000)
        self.assertFalse(verdict.approved)
        self.assertIn("سقف پوزیشن", verdict.reason)

    def test_the_monitor_reports_the_var_it_used(self):
        mon = pr.PortfolioRiskMonitor(max_open_positions=5, max_var_pct=0.99)
        a = [0.01, -0.01] * 25
        b = [-0.01, 0.01] * 25
        verdict = mon.evaluate_portfolio_risk(
            [pr.OpenPosition("A", 1, 100, 101)], 100000,
            returns_by_symbol={"A": a, "B": b}, weights={"A": 0.5, "B": 0.5})
        self.assertTrue(verdict.approved)
        self.assertIsNotNone(verdict.var_pct)
        self.assertIn("VaR", verdict.reason)

    def test_no_real_diversification_is_refused(self):
        mon = pr.PortfolioRiskMonitor(max_open_positions=5, max_var_pct=0.99)
        same = [0.01, -0.01] * 25
        verdict = mon.evaluate_portfolio_risk(
            [pr.OpenPosition("A", 1, 100, 100), pr.OpenPosition("B", 1, 100, 100)], 100000,
            returns_by_symbol={"A": same, "B": same}, weights={"A": 0.5, "B": 0.5})
        self.assertFalse(verdict.approved)
        self.assertIn("تنوع", verdict.reason)


class ApiTests(unittest.TestCase):
    def test_health_reports_real_coverage(self):
        h = api.health()
        self.assertEqual(h["status"], "ok")
        self.assertGreater(h["instruments"], 300)

    def test_questionnaire_is_json_ready(self):
        q = api.questionnaire()
        self.assertEqual(q["count"], len(q["questions"]))
        first = q["questions"][0]
        self.assertIn("options", first)
        self.assertTrue(all("label" in o and "value" in o for o in first["options"]))

    def test_onboarding_without_capital_is_refused(self):
        with self.assertRaises(ValueError):
            api.onboard({"answers": answers(), "capital": 0})

    def test_onboarding_returns_profile_allocation_and_holdings(self):
        out = api.onboard({"answers": answers(3), "capital": 1_000_000,
                           "paid_until": "2030-01-01", "today": "2026-11-15"})
        self.assertAlmostEqual(sum(out["allocation"].values()), 1.0, places=6)
        self.assertTrue(out["holdings"])
        self.assertTrue(out["subscription"]["allowed"])
        self.assertIn("disclaimer", out)

    def test_expired_subscription_stops_the_advice(self):
        out = api.onboard({"answers": answers(3), "capital": 1_000_000,
                           "paid_until": "2026-01-01", "today": "2026-11-15"})
        self.assertFalse(out["subscription"]["allowed"])

    def test_rebalance_lists_explicit_trades(self):
        out = api.rebalance({"answers": answers(4), "capital": 1_000_000,
                             "current": {"equity": 0.10}})
        self.assertTrue(out["trades"])
        self.assertIn("bucket", out["trades"][0])

    def test_venue_status_answers_for_a_real_symbol(self):
        out = api.venue_status("SPY", "2026-11-18T15:00:00+00:00")
        self.assertIn("open", out)
        self.assertIn(out["open"], (True, False))


if __name__ == "__main__":
    unittest.main()
