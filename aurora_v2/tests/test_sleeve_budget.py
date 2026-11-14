import unittest

from aurora.strategies.cross_asset import CrossAssetRules, sized_weights

SLEEVE_SHARE = 0.30


class SleeveBudgetTests(unittest.TestCase):
    def test_sleeve_can_never_exceed_its_budget(self):
        """The share is a ceiling on the sleeve, not a target the sleeve may drift past."""
        feats = {f"A{i}": {"momentum": 0.2, "vol": 0.10 + i * 0.01} for i in range(12)}
        w = sized_weights(feats, CrossAssetRules())
        scaled = {k: v * SLEEVE_SHARE for k, v in w.items()}
        self.assertLessEqual(sum(scaled.values()), SLEEVE_SHARE + 1e-9)

    def test_a_fully_invested_sleeve_buys_nothing_when_nothing_qualifies(self):
        feats = {"DOWN": {"momentum": -0.1, "vol": 0.2},
                 "FLATVOL": {"momentum": 0.3, "vol": 0.0}}
        self.assertEqual(sized_weights(feats, CrossAssetRules()), {})

    def test_per_asset_cap_survives_being_scaled_down(self):
        w = sized_weights({"ONLY": {"momentum": 0.3, "vol": 0.2}}, CrossAssetRules())
        self.assertAlmostEqual(w["ONLY"] * SLEEVE_SHARE, 0.35 * SLEEVE_SHARE, places=9)

    def test_remaining_budget_is_cash_not_leverage(self):
        w = sized_weights({"ONLY": {"momentum": 0.3, "vol": 0.2}}, CrossAssetRules())
        cash = SLEEVE_SHARE - sum(v * SLEEVE_SHARE for v in w.values())
        self.assertGreater(cash, 0)
        self.assertAlmostEqual(cash, SLEEVE_SHARE * 0.65, places=9)


if __name__ == "__main__":
    unittest.main()
