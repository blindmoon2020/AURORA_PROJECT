import math
import unittest

from aurora.advisory.recommender import (COST_VETO_BPS, MIN_HISTORY, WEIGHTS, explain,
                                         momentum, recommend, trend, annual_vol)


def series(start, drift, days=320, vol=0.01):
    """A deterministic geometric path; no randomness, so tests cannot flake."""
    prices, price = [], start
    for i in range(days):
        price *= (1 + drift + vol * math.sin(i / 7.0))
        prices.append(price)
    return prices


PRICES = {
    "SPY": series(400, 0.0006),
    "AAPL": series(150, 0.0012),
    "KO": series(55, 0.0002),
    "GLD": series(180, 0.0008, vol=0.006),
    "ZC": series(480, -0.0004),
}


class MeasurementTests(unittest.TestCase):
    def test_momentum_needs_one_year_plus_the_skipped_month(self):
        self.assertIsNone(momentum(series(100, 0.001, days=200)))
        self.assertIsNotNone(momentum(series(100, 0.001, days=MIN_HISTORY + 21)))

    def test_a_rising_series_has_positive_momentum_and_trend(self):
        self.assertGreater(momentum(series(100, 0.002)), 0)
        self.assertGreater(trend(series(100, 0.002)), 0)

    def test_a_falling_series_has_negative_trend(self):
        self.assertLess(trend(series(100, -0.002)), 0)

    def test_volatility_is_annualised_and_positive(self):
        self.assertGreater(annual_vol(series(100, 0.001)), 0.1)

    def test_volatility_needs_enough_observations(self):
        self.assertIsNone(annual_vol(series(100, 0.001, days=30)))


class RankingTests(unittest.TestCase):
    def test_the_stronger_asset_ranks_first(self):
        p = recommend(PRICES)
        scores = {r.symbol: r.score for r in p.recommendations}
        self.assertGreater(scores["AAPL"], scores["ZC"])

    def test_the_same_input_produces_the_same_output(self):
        a, b = recommend(PRICES), recommend(PRICES)
        self.assertEqual([(r.symbol, r.score, r.action) for r in a.recommendations],
                         [(r.symbol, r.score, r.action) for r in b.recommendations])

    def test_a_falling_asset_is_avoided_with_a_reason(self):
        p = recommend(PRICES)
        zc = next(r for r in p.recommendations if r.symbol == "ZC")
        self.assertIn(zc.action, ("پرهیز", "نگهداری"))
        self.assertEqual(zc.target_weight, 0.0)
        self.assertTrue(any("مومنتوم" in reason for reason in zc.reasons))

    def test_every_recommendation_carries_numbers_not_adjectives(self):
        p = recommend(PRICES)
        for rec in p.recommendations:
            if rec.action == "داده ناکافی":
                continue
            self.assertTrue(any("%" in reason for reason in rec.reasons), rec.symbol)


class BudgetTests(unittest.TestCase):
    def test_no_leverage_ever(self):
        p = recommend(PRICES, risk_scale=1.0)
        self.assertLessEqual(sum(p.weights.values()), 1.0)
        self.assertGreaterEqual(p.cash, 0.0)

    def test_the_brake_scale_caps_the_proposal(self):
        full = recommend(PRICES, risk_scale=1.0)
        braked = recommend(PRICES, risk_scale=0.5)
        self.assertLessEqual(sum(braked.weights.values()), sum(full.weights.values()))
        self.assertAlmostEqual(sum(braked.weights.values()), sum(full.weights.values()) / 2, delta=0.01)

    def test_an_invalid_scale_is_refused(self):
        for bad in (0.0, 1.5, -0.2):
            with self.assertRaises(ValueError):
                recommend(PRICES, risk_scale=bad)

    def test_a_single_instrument_is_capped(self):
        p = recommend({"AAPL": PRICES["AAPL"], "KO": PRICES["KO"]})
        for weight in p.weights.values():
            self.assertLessEqual(weight, 0.25 + 1e-9)

    def test_crypto_cannot_exceed_its_class_cap(self):
        crypto = {"BTC-USD": series(100, 0.004), "ETH-USD": series(50, 0.005)}
        p = recommend({**PRICES, **crypto}, risk_scale=1.0)
        crypto_weight = sum(w for s, w in p.weights.items() if s in crypto)
        self.assertLessEqual(crypto_weight, 0.10 + 1e-9)


class HonestyTests(unittest.TestCase):
    def test_an_unknown_symbol_raises_instead_of_being_ranked(self):
        from aurora.core.asset_universe import UnknownInstrument
        with self.assertRaises(UnknownInstrument):
            recommend({"NOT-REAL": series(100, 0.001)})

    def test_short_history_is_named_not_scored_as_zero(self):
        p = recommend({"AAPL": series(150, 0.001, days=90)})
        self.assertEqual(p.recommendations[0].action, "داده ناکافی")
        self.assertTrue(any("تاریخچه" in w for w in p.recommendations[0].warnings))

    def test_absent_fundamentals_are_declared_and_reweighted(self):
        p = recommend(PRICES)                      # no fundamentals at all
        self.assertTrue(any("بنیادی" in n for n in p.notes))
        # the pre-registered weight table itself is untouched: the absence is handled in
        # the run, not by editing the rule
        self.assertEqual(WEIGHTS["fundamental"], 0.20)

    def test_a_high_cost_instrument_is_vetoed_with_the_number(self):
        p = recommend(PRICES, cost_bps={"AAPL": COST_VETO_BPS + 40})
        aapl = next(r for r in p.recommendations if r.symbol == "AAPL")
        self.assertEqual(aapl.action, "پرهیز")
        self.assertEqual(aapl.target_weight, 0.0)
        self.assertTrue(any("bps" in w for w in aapl.warnings))

    def test_an_unverified_instrument_is_flagged(self):
        p = recommend({**PRICES, "SAND-USD": series(3, 0.003)})
        sand = next((r for r in p.recommendations if r.symbol == "SAND-USD"), None)
        if sand and sand.action != "داده ناکافی":
            self.assertTrue(any("تأییدنشده" in w for w in sand.warnings))

    def test_the_report_states_that_no_edge_is_claimed(self):
        text = explain(recommend(PRICES))
        self.assertIn("ادعای بازده برتر", text)
        self.assertIn("۰.۰۶", text)


if __name__ == "__main__":
    unittest.main()
