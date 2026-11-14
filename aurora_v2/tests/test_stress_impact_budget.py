import unittest

from aurora.execution.impact import (ImpactEstimate, Latency, estimate, latency_report,
                                     participation, slippage_vs_impact, split_order)
from aurora.portfolio.risk_budget import (concentration_check, correlation, covariance_matrix,
                                          diversification_ratio, equal_risk_weights,
                                          portfolio_vol, risk_contributions,
                                          stressed_covariance, to_crisis_weights)
from aurora.portfolio.stress import (block_bootstrap, bootstrap, correlated_shock,
                                     cost_shock, liquidation_days)


class BootstrapTests(unittest.TestCase):
    def test_same_seed_same_answer(self):
        rets = [0.01, -0.02, 0.015, -0.005] * 30
        a = bootstrap(rets, paths=50, seed=3)
        b = bootstrap(rets, paths=50, seed=3)
        self.assertEqual(a.worst_dd_pct, b.worst_dd_pct)

    def test_a_strategy_full_of_big_losses_shows_bad_drawdown(self):
        calm = [0.001, 0.001, 0.001, -0.001] * 40
        brutal = [-0.15] * 5 + [0.005] * 35
        self.assertGreater(bootstrap(brutal, paths=100).p95_dd_pct,
                           bootstrap(calm, paths=100).p95_dd_pct)

    def test_breach_rate_is_a_share_not_a_count(self):
        res = bootstrap([-0.2] * 4 + [0.05] * 20, paths=40, limit_pct=10)
        self.assertGreaterEqual(res.breach_rate, 0.0)
        self.assertLessEqual(res.breach_rate, 1.0)

    def test_block_bootstrap_keeps_contiguous_losses(self):
        rets = [-0.1] * 12 + [0.02] * 48
        self.assertGreater(block_bootstrap(rets, paths=80, block=6).worst_dd_pct, 0)

    def test_empty_returns_is_an_error_not_a_zero(self):
        with self.assertRaises(ValueError):
            bootstrap([])

    def test_cost_shock_reports_each_multiple(self):
        out = cost_shock([0.004] * 60, 0.0005)
        self.assertEqual(set(out), {"1x", "2x", "3x", "5x", "8x"})
        self.assertGreater(out["1x"]["mean_pct"], out["8x"]["mean_pct"])

    def test_correlated_shock_assumes_loss_when_exposure_unknown(self):
        loss = correlated_shock({"A": 1.0}, {}, crisis_correlation=1.0)
        self.assertAlmostEqual(loss, -0.20)

    def test_liquidation_days_refuses_unknown_liquidity(self):
        self.assertEqual(liquidation_days(1000, 0), float("inf"))
        self.assertAlmostEqual(liquidation_days(1000, 1000, 0.10), 10.0)


class ImpactTests(unittest.TestCase):
    def test_impact_grows_with_size(self):
        small = estimate(1e5, 1e8, daily_vol_bps=150)
        big = estimate(5e6, 1e8, daily_vol_bps=150)
        self.assertGreater(big.impact_bps, small.impact_bps)

    def test_impact_grows_with_volatility(self):
        calm = estimate(1e6, 1e8, daily_vol_bps=50)
        wild = estimate(1e6, 1e8, daily_vol_bps=400)
        self.assertGreater(wild.impact_bps, calm.impact_bps)

    def test_square_root_law_halves_impact_at_quarter_size(self):
        a = estimate(4e6, 1e8, 100).impact_bps
        b = estimate(1e6, 1e8, 100).impact_bps
        self.assertAlmostEqual(a, 2 * b, places=9)

    def test_unknown_adv_is_refused_not_defaulted(self):
        est = estimate(1e6, None, 100)
        self.assertFalse(est.allowed)
        self.assertIn("liquidity is unknown", est.reason)

    def test_order_above_cap_is_refused(self):
        est = estimate(2e7, 1e8, 100)
        self.assertFalse(est.allowed)
        self.assertGreater(est.participation, 0.10)

    def test_split_order_breaks_an_oversized_order_into_days(self):
        plan = split_order(3e7, 1e8, 100)
        self.assertGreater(plan["slices"], 1)
        self.assertAlmostEqual(plan["days"], plan["slices"])

    def test_split_of_a_small_order_is_one_slice(self):
        self.assertEqual(split_order(1e6, 1e8, 100)["slices"], 1)

    def test_zero_adv_means_no_participation(self):
        self.assertIsNone(participation(1000, 0))

    def test_latency_reports_breaches(self):
        samples = [Latency(1, 2, "auto"), Latency(30, 1200, "manual")]  # 20.5 min manual
        rep = latency_report(samples)
        self.assertEqual(rep["breaches"], 1)

    def test_latency_of_no_samples_is_zero_not_a_crash(self):
        self.assertEqual(latency_report([])["samples"], 0)

    def test_slippage_check_calls_out_an_underestimate(self):
        est = estimate(1e6, 1e8, 100)
        self.assertIn("underestimated", slippage_vs_impact(est.total_bps + 60, est))


class RiskBudgetTests(unittest.TestCase):
    def _series(self):
        return {"eq": [0.01, -0.008, 0.012, 0.004, -0.003] * 20,
                "bond": [-0.002, 0.003, -0.001, 0.002, 0.001] * 20,
                "gold": [0.004, 0.006, -0.005, 0.003, 0.002] * 20}

    def test_correlation_of_a_series_with_itself_is_one(self):
        s = self._series()["eq"]
        self.assertAlmostEqual(correlation(s, s), 1.0, places=9)

    def test_flat_series_has_no_correlation_rather_than_a_crash(self):
        self.assertEqual(correlation([0.0] * 30, [0.1, -0.1] * 15), 0.0)

    def test_equal_risk_weights_are_equal_when_assets_match(self):
        series = {"a": [0.01, -0.01] * 30, "b": [0.01, -0.01] * 30}
        w = equal_risk_weights(covariance_matrix(series))
        self.assertAlmostEqual(w["a"], 0.5, places=6)

    def test_low_vol_asset_gets_more_capital(self):
        series = {"calm": [0.001, -0.001] * 30, "wild": [0.05, -0.05] * 30}
        w = equal_risk_weights(covariance_matrix(series))
        self.assertGreater(w["calm"], w["wild"])

    def test_equal_risk_gives_each_asset_the_same_risk_budget(self):
        # ERC condition is w_i * (Cw)_i equal across sleeves; risk *shares* can be
        # negative for a hedge, so comparing shares would test the wrong thing
        cov = covariance_matrix(self._series())
        w = equal_risk_weights(cov)
        contrib = {a: w[a] * sum(cov[a][b] * w[b] for b in w) for a in w}
        spread = max(contrib.values()) - min(contrib.values())
        scale = max(abs(v) for v in contrib.values())
        self.assertLess(spread / scale, 1e-6)

    def test_weights_sum_to_one(self):
        w = equal_risk_weights(covariance_matrix(self._series()))
        self.assertAlmostEqual(sum(w.values()), 1.0, places=9)

    def test_zero_vol_asset_is_excluded(self):
        self.assertNotIn("dead", equal_risk_weights(covariance_matrix(
            {"live": [0.01, -0.01] * 30, "dead": [0.0] * 60})))

    def test_stressed_covariance_raises_correlations_only(self):
        cov = covariance_matrix(self._series())
        stressed = stressed_covariance(cov, 0.9)
        self.assertGreaterEqual(portfolio_vol({"eq": .5, "bond": .5}, stressed),
                                portfolio_vol({"eq": .5, "bond": .5}, cov) - 1e-12)

    def test_crisis_rebudget_does_not_become_one_big_bet(self):
        cov = covariance_matrix(self._series())
        calm_w = equal_risk_weights(cov)
        crisis_w = to_crisis_weights(calm_w, cov, 0.9)
        self.assertLess(max(crisis_w.values()), 0.75)

    def test_diversification_ratio_is_one_for_one_asset(self):
        cov = covariance_matrix({"a": [0.01, -0.01] * 30})
        self.assertAlmostEqual(diversification_ratio({"a": 1.0}, cov), 1.0)

    def test_concentration_check_flags_one_dominant_risk(self):
        cov = covariance_matrix({"a": [0.05, -0.05] * 30, "b": [0.001, -0.001] * 30})
        ok, worst, _ = concentration_check({"a": 0.5, "b": 0.5}, cov)
        self.assertFalse(ok)
        self.assertGreater(worst, 0.55)


if __name__ == "__main__":
    unittest.main()
