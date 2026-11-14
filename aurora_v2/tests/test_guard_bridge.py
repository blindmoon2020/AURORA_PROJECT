import unittest

from aurora.core.types import Side
from aurora.execution.manual import FillRecord, ManualExecutionError
from aurora.execution.manual_bridge import book_from_fills, session_summary, tickets_for_targets
from aurora.portfolio.guard import GuardLimits, apply_limits


class GuardTests(unittest.TestCase):
    def test_risk_off_blocks_everything(self):
        r = apply_limits({"AAPL": 0.1, "MSFT": 0.1}, GuardLimits(), risk_off=True)
        self.assertEqual(r.allowed, {})
        self.assertEqual(sorted(r.blocked_symbols), ["AAPL", "MSFT"])

    def test_name_cap_trims_and_says_so(self):
        r = apply_limits({"AAPL": 0.40}, GuardLimits(max_weight=0.15))
        self.assertAlmostEqual(r.allowed["AAPL"], 0.15)
        self.assertTrue(any("name cap" in n for n in r.notes))

    def test_dust_is_dropped_not_invested(self):
        r = apply_limits({"AAPL": 0.10, "F": 0.002}, GuardLimits(min_trade_weight=0.01))
        self.assertIn("AAPL", r.allowed)
        self.assertNotIn("F", r.allowed)
        self.assertEqual(r.blocked_symbols, ["F"])

    def test_gross_is_scaled_to_budget(self):
        targets = {s: 0.15 for s in ("A", "B", "C", "D", "E", "F", "G", "H")}
        r = apply_limits(targets, GuardLimits(max_gross=1.0))
        self.assertLessEqual(sum(r.allowed.values()), 1.0 + 1e-12)

    def test_name_count_keeps_the_largest(self):
        targets = {"A": 0.05, "B": 0.04, "C": 0.03, "D": 0.02}
        r = apply_limits(targets, GuardLimits(max_names=2))
        self.assertEqual(sorted(r.allowed), ["A", "B"])
        self.assertEqual(len(r.blocked), 2)


class BridgeTests(unittest.TestCase):
    def test_units_follow_weight_and_price(self):
        t = tickets_for_targets({"AAPL": 0.10}, {"AAPL": 100.0}, 10_000.0, "D1", 1000)[0]
        self.assertAlmostEqual(t.units, 10.0)
        self.assertEqual(t.expires_ts, 1000 + 6 * 3600)

    def test_missing_price_is_refused(self):
        with self.assertRaises(ManualExecutionError):
            tickets_for_targets({"AAPL": 0.1, "ZZZ": 0.1}, {"AAPL": 100.0}, 10_000.0, "D1", 1000)

    def test_limit_buffer_raises_the_cap(self):
        t = tickets_for_targets({"A": 0.1}, {"A": 50.0}, 5_000.0, "D1", 1,
                                limit_buffer_bps=20)[0]
        self.assertAlmostEqual(t.limit_price, 50.0 * 1.002)

    def test_fills_become_weights(self):
        fills = [FillRecord("D1-01", 100, "AAPL", Side.LONG, 10, 100.0),
                 FillRecord("D1-02", 100, "MSFT", Side.LONG, 5, 100.0)]
        w = book_from_fills(fills, 10_000.0)
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertAlmostEqual(w["AAPL"], 1000 / 1500)

    def test_session_summary_reports_unfilled(self):
        t = tickets_for_targets({"A": 0.1, "B": 0.1}, {"A": 10.0, "B": 10.0}, 1000.0, "D1", 0)
        summary = session_summary(t, [])
        self.assertIn("unfilled", summary)


if __name__ == "__main__":
    unittest.main()
