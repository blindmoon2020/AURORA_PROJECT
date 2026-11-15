import tempfile
import unittest
from pathlib import Path

from aurora.advice import onboarding as ob
from aurora.core.types import Candle
from aurora.data.data_cache import CandleCache


def answers(**over):
    base = {"horizon": 4, "emergency": 4, "income": 4, "share": 4,
            "drawdown": 4, "experience": 4, "goal": 4}
    base.update(over)
    return base


def bars(n=5, start=1700000000):
    return [Candle(ts=start + i * 86400, open=10 + i, high=11 + i, low=9 + i, close=10.5 + i,
                   volume=100 + i) for i in range(n)]


class ProfileTests(unittest.TestCase):
    def test_a_cautious_client_gets_the_lowest_cap(self):
        p = ob.score_answers(answers(horizon=0, emergency=0, income=0, share=0,
                                     drawdown=0, experience=0, goal=0))
        self.assertEqual(p.band, "محافظه‌کار")
        self.assertLessEqual(p.risk_asset_cap, 0.20)

    def test_a_client_who_cannot_sleep_is_limited_by_tolerance_not_capacity(self):
        # young, long horizon, big emergency fund (capacity high) but panics in a drawdown
        p = ob.score_answers(answers(drawdown=0, experience=0, goal=0))
        self.assertEqual(p.binding, "تحمل")
        self.assertLess(p.risk_asset_cap, 0.60)

    def test_capacity_limits_when_tolerance_is_generous(self):
        p = ob.score_answers(answers(horizon=0, emergency=0, income=0, share=0))
        self.assertEqual(p.binding, "ظرفیت")

    def test_the_binding_number_is_the_lower_of_the_two(self):
        p = ob.score_answers(answers(horizon=0, emergency=0, income=0, share=0))
        self.assertLessEqual(p.score, min(p.capacity_score, p.tolerance_score) + 1e-9)

    def test_disagreement_between_the_two_is_named(self):
        p = ob.score_answers(answers(drawdown=0, experience=0, goal=0))
        self.assertTrue(any("اختلاف" in r for r in p.reasons))

    def test_invalid_option_index_is_rejected(self):
        with self.assertRaises(ValueError):
            ob.score_answers(answers(horizon=99))

    def test_empty_questionnaire_is_rejected_not_defaulted(self):
        with self.assertRaises(ValueError):
            ob.score_answers({})

    def test_missing_tolerance_section_cannot_produce_a_profile(self):
        with self.assertRaises(ValueError):
            ob.score_answers({"horizon": 4, "emergency": 4, "income": 4, "share": 4})

    def test_unanswered_questions_are_reported(self):
        partial = {k: v for k, v in answers().items() if k != "goal"}
        p = ob.score_answers(partial)
        self.assertTrue(any("goal" in r for r in p.reasons))


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.conservative = ob.score_answers(answers(horizon=0, emergency=0, income=0, share=0,
                                                     drawdown=0, experience=0, goal=0))
        self.aggressive = ob.score_answers(answers())

    def test_weights_sum_to_one(self):
        for p in (self.conservative, self.aggressive):
            self.assertAlmostEqual(sum(ob.design_portfolio(p).values()), 1.0, places=6)

    def test_risk_assets_never_exceed_the_profile_cap(self):
        for p in (self.conservative, self.aggressive):
            alloc = ob.design_portfolio(p)
            risky = sum(v for k, v in alloc.items() if k in {"equity", "commodity", "crypto", "other"})
            self.assertLessEqual(risky, p.risk_asset_cap + 1e-9)

    def test_a_cautious_client_holds_more_cash_than_an_aggressive_one(self):
        self.assertGreater(ob.design_portfolio(self.conservative)["cash"],
                           ob.design_portfolio(self.aggressive)["cash"])

    def test_the_market_brake_scales_risk_down(self):
        full = ob.design_portfolio(self.aggressive, risk_scale=1.0)
        braked = ob.design_portfolio(self.aggressive, risk_scale=0.5)
        risky = lambda a: sum(v for k, v in a.items() if k in {"equity", "commodity", "crypto"})
        self.assertLess(risky(braked), risky(full))

    def test_leverage_scale_is_refused(self):
        with self.assertRaises(ValueError):
            ob.design_portfolio(self.aggressive, risk_scale=1.5)


class RebalanceTests(unittest.TestCase):
    def test_a_drift_inside_the_band_produces_no_trade(self):
        trades = ob.rebalance({"equity": 0.50}, {"equity": 0.51}, capital=100_000)
        self.assertEqual(trades, [])

    def test_a_real_gap_produces_a_sized_trade(self):
        trades = ob.rebalance({"equity": 0.30}, {"equity": 0.50}, capital=100_000)
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].side, "افزودن")
        self.assertAlmostEqual(trades[0].amount, 20_000, places=2)

    def test_a_cut_is_reported_as_a_reduction(self):
        trades = ob.rebalance({"crypto": 0.20}, {"crypto": 0.05}, capital=100_000)
        self.assertEqual(trades[0].side, "کاهش")
        self.assertAlmostEqual(trades[0].amount, -15_000, places=2)

    def test_a_tiny_trade_is_skipped_because_cost_beats_value(self):
        trades = ob.rebalance({"cash": 0.50}, {"cash": 0.53}, capital=100, band=0.001,
                              min_amount=1.0, cost_bps=500)
        self.assertEqual(trades, [])

    def test_zero_capital_is_refused(self):
        with self.assertRaises(ValueError):
            ob.rebalance({}, {}, capital=0)


class SubscriptionTests(unittest.TestCase):
    def test_an_active_subscription_allows_advice(self):
        self.assertTrue(ob.subscription_gate("2026-12-01", "2026-11-15").allowed)

    def test_a_lapsed_subscription_freezes_the_portfolio(self):
        access = ob.subscription_gate("2026-10-01", "2026-11-15")
        self.assertFalse(access.allowed)
        self.assertGreater(access.stale_days, 3)

    def test_a_short_gap_is_a_grace_period_not_a_freeze(self):
        access = ob.subscription_gate("2026-11-14", "2026-11-15")
        self.assertTrue(access.allowed)
        self.assertEqual(access.stale_days, 1)

    def test_no_subscription_means_no_advice(self):
        self.assertFalse(ob.subscription_gate(None, "2026-11-15").allowed)

    def test_a_bad_date_is_an_error_not_a_guess(self):
        with self.assertRaises(ValueError):
            ob.subscription_gate("not-a-date", "2026-11-15")


class ReportTests(unittest.TestCase):
    def test_the_report_carries_the_disclaimer_and_the_numbers(self):
        p = ob.score_answers(answers())
        alloc = ob.design_portfolio(p)
        trades = ob.rebalance({"equity": 0.10}, alloc, capital=50_000)
        text = ob.onboarding_report(p, alloc, 50_000, trades,
                                    ob.subscription_gate("2027-01-01", "2026-11-15"))
        self.assertIn("وعده بازده", text)
        self.assertIn(p.band, text)
        self.assertIn("۵۰,۰۰۰", text)


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "c.db"
        self.cache = CandleCache(self.tmp)

    def test_roundtrip_returns_bars_oldest_first(self):
        self.assertEqual(self.cache.put("AAPL", "1d", bars(3)), 3)
        got = self.cache.get("AAPL", "1d")
        self.assertEqual([b["ts"] for b in got], sorted(b["ts"] for b in got))
        self.assertEqual(len(got), 3)

    def test_the_same_bar_is_not_stored_twice(self):
        self.cache.put("AAPL", "1d", bars(3))
        self.assertEqual(self.cache.put("AAPL", "1d", bars(3)), 0)
        self.assertEqual(len(self.cache.get("AAPL", "1d")), 3)

    def test_new_bars_are_appended(self):
        self.cache.put("AAPL", "1d", bars(3))
        self.assertEqual(self.cache.put("AAPL", "1d", bars(5)), 2)

    def test_an_unknown_symbol_returns_empty_not_an_error(self):
        self.assertEqual(self.cache.get("NOPE", "1d"), [])

    def test_staleness_is_measured_in_hours(self):
        self.cache.put("AAPL", "1d", bars(1))
        last = self.cache.last_ts("AAPL", "1d")
        self.assertAlmostEqual(self.cache.stale_hours("AAPL", "1d", last + 7200), 2.0)

    def test_stats_count_rows_and_symbols(self):
        self.cache.put("AAPL", "1d", bars(2))
        self.cache.put("MSFT", "1d", bars(2))
        s = self.cache.stats()
        self.assertEqual((s.rows, s.symbols), (4, 2))


if __name__ == "__main__":
    unittest.main()
