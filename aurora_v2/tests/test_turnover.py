import unittest

from aurora.portfolio.turnover import (Band, apply_band, break_even_edge, sweep,
                                       trade_cost, turnover)


class BandTests(unittest.TestCase):
    def test_small_drift_is_left_alone(self):
        adj, skipped = apply_band({"A": 0.10}, {"A": 0.11}, Band(abs_band=0.02, rel_band=0.25))
        self.assertEqual(adj["A"], 0.10)
        self.assertIn("inside band", skipped["A"])

    def test_large_drift_is_traded(self):
        adj, skipped = apply_band({"A": 0.10}, {"A": 0.20}, Band(abs_band=0.02, rel_band=0.25))
        self.assertEqual(adj["A"], 0.20)
        self.assertNotIn("A", skipped)

    def test_exit_is_never_band_limited(self):
        adj, _ = apply_band({"A": 0.10}, {}, Band(abs_band=0.50, rel_band=0.90))
        self.assertEqual(adj["A"], 0.0)

    def test_new_position_is_always_taken(self):
        adj, _ = apply_band({}, {"B": 0.03}, Band(abs_band=0.50, rel_band=0.90))
        self.assertEqual(adj["B"], 0.03)

    def test_dust_is_not_traded_even_outside_the_band(self):
        adj, skipped = apply_band({"A": 0.10}, {"A": 0.105}, Band(abs_band=0.0, min_trade_weight=0.01))
        self.assertEqual(adj["A"], 0.10)
        self.assertIn("A", skipped)

    def test_untouched_weights_produce_no_turnover(self):
        adj, _ = apply_band({"A": 0.10, "B": 0.10}, {"A": 0.105, "B": 0.098},
                            Band(abs_band=0.02, rel_band=0.25))
        self.assertEqual(turnover({"A": 0.10, "B": 0.10}, adj), 0.0)


class CostTests(unittest.TestCase):
    def test_turnover_is_one_way(self):
        self.assertAlmostEqual(turnover({"A": 0.1}, {"A": 0.3}), 0.1)

    def test_trade_cost_uses_the_market_schedule(self):
        self.assertAlmostEqual(trade_cost(0.2, 0.0124), 0.00248, places=8)

    def test_iran_fees_make_monthly_churn_obvious(self):
        # full turnover every month on the Tehran schedule is unaffordable
        self.assertGreater(break_even_edge(1.0, 0.0124), 0.10)

    def test_sweep_shows_cost_falling_as_the_band_widens(self):
        rows = sweep({"A": 0.5, "B": 0.5}, {"A": 0.55, "B": 0.45}, 0.0124)
        self.assertGreaterEqual(rows[0]["turnover"], rows[-1]["turnover"])
        self.assertEqual(rows[0]["band"], 0.0)


if __name__ == "__main__":
    unittest.main()
