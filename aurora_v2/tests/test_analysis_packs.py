import math
import unittest

from aurora.core.types import Candle
from aurora.analysis import combine as cb
from aurora.analysis import technical as tech
from aurora.analysis import fundamental as fund


def bars(n=300, drift=0.001, wave=0.03, start=100.0):
    out = []
    for i in range(n):
        px = start * (1 + drift) ** i * (1 + wave * math.sin(2 * math.pi * i / 40))
        out.append(Candle(ts=1700000000 + i * 86400, open=px, high=px * 1.006,
                          low=px * 0.994, close=px, volume=1_000_000 + i))
    return out


class TechnicalPackTests(unittest.TestCase):
    def test_every_method_declares_a_family(self):
        for name, fn in tech.EVALUATORS.items():
            v = fn(bars())
            if v is not None:
                self.assertIn(v.family, {"structure", "trend", "momentum", "breakout",
                                         "mean_reversion", "flow"})

    def test_short_history_drops_a_method_instead_of_scoring_zero(self):
        short = bars(n=30)
        self.assertIsNone(tech.EVALUATORS["trend"](short))

    def test_a_rising_market_gets_positive_structure_and_trend(self):
        verdicts = {v.method: v for v in tech.evaluate_all(bars())}
        self.assertGreater(verdicts["structure"].score, 0)
        self.assertGreater(verdicts["trend"].score, 0)

    def test_a_falling_market_gets_negative_scores(self):
        verdicts = {v.method: v for v in tech.evaluate_all(bars(drift=-0.001))}
        self.assertLess(verdicts["structure"].score, 0)

    def test_scores_stay_inside_the_band(self):
        for v in tech.evaluate_all(bars(wave=0.08)):
            self.assertGreaterEqual(v.score, -1.0)
            self.assertLessEqual(v.score, 1.0)

    def test_metals_prior_favours_structure_over_momentum(self):
        bias = tech.METHOD_CLASS_BIAS["metals"]
        self.assertGreater(bias["structure"], bias["momentum"])

    def test_fx_prior_favours_trend(self):
        self.assertGreaterEqual(tech.METHOD_CLASS_BIAS["fx"]["trend"],
                                tech.METHOD_CLASS_BIAS["fx"]["structure"])


class FundamentalPackTests(unittest.TestCase):
    def test_a_cheap_profitable_company_scores_positive(self):
        s = fund.score_company({"pe": 12, "pb": 1.2, "roe": 0.20, "margin": 0.18,
                                "debt_to_equity": 0.5, "revenue_growth": 0.2})
        self.assertGreater(s.score, 0.5)
        self.assertEqual(s.confidence, 1.0)

    def test_negative_pe_is_not_a_bargain(self):
        s = fund.score_company({"pe": -8})
        self.assertNotIn("pe", s.components)

    def test_missing_metrics_lower_confidence_not_the_score_direction(self):
        s = fund.score_company({"pe": 40})
        self.assertLess(s.confidence, 1.0)
        self.assertLess(s.score, 0)

    def test_no_metrics_is_named_not_scored(self):
        s = fund.score_company({})
        self.assertEqual(s.confidence, 0.0)
        self.assertTrue(s.warnings)

    def test_real_yields_work_against_gold(self):
        s = fund.macro_score("metals", {"real_yield": 1.0})
        self.assertLess(s.score, 0)

    def test_rising_pmi_supports_energy(self):
        s = fund.macro_score("energy", {"pmi": 1.0})
        self.assertGreater(s.score, 0)

    def test_unknown_class_says_so_instead_of_guessing(self):
        s = fund.macro_score("nft", {"pmi": 1.0})
        self.assertEqual(s.confidence, 0.0)


class CombineTests(unittest.TestCase):
    def test_weights_are_blended_by_class(self):
        self.assertEqual(sum(cb.BLEND["equity"]), 1.0)
        self.assertEqual(sum(cb.BLEND["fx"]), 1.0)

    def test_regime_separates_a_trend_from_a_range(self):
        self.assertEqual(cb.regime_of(bars(drift=0.004, wave=0.005)), cb.TRENDING)

    def test_the_selector_prefers_mean_reversion_in_a_range(self):
        ranked = dict((n, w) for n, w, _ in cb.select("fx", cb.RANGING))
        trend_ranked = dict((n, w) for n, w, _ in cb.select("fx", cb.TRENDING))
        self.assertGreater(ranked["mean_reversion"], trend_ranked["mean_reversion"])

    def test_measured_fitness_can_beat_the_prior(self):
        prior = dict((n, w) for n, w, _ in cb.select("metals", cb.RANGING))["mean_reversion"]
        ranked = dict((n, w) for n, w, _ in cb.select("metals", cb.RANGING,
                                                     fitness={"mean_reversion": (2.0, 500)}))
        # 500 observations must drag the weight toward the measured 2.0, past the prior
        self.assertGreater(ranked["mean_reversion"], prior)
        self.assertGreater(ranked["mean_reversion"], 1.5)

    def test_a_conflict_halves_the_position(self):
        view = cb.combine("GLD", "metals", bars(drift=-0.003),
                          metrics={"pe": 8, "roe": 0.25, "margin": 0.2})
        if view.conflicts:
            self.assertEqual(view.size_multiplier, 0.5)
        else:
            self.assertEqual(view.size_multiplier, 1.0)

    def test_absent_fundamentals_are_announced(self):
        view = cb.combine("SPY", "etf", bars())
        self.assertTrue(any("بنیادی" in n for n in view.notes))

    def test_the_report_carries_both_sections(self):
        view = cb.combine("SPY", "etf", bars(), metrics={"pe": 20, "roe": 0.2},
                          drivers={"real_yield": -0.5})
        text = cb.explain(view)
        self.assertIn("تکنیکال", text)
        self.assertIn("بنیادی", text)
        self.assertIn("ماکرو", text)


if __name__ == "__main__":
    unittest.main()
