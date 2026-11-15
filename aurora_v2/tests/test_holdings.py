import unittest

from aurora.advice import holdings as hd


class ExpandTests(unittest.TestCase):
    def test_every_riyal_of_the_allocation_reaches_a_named_row(self):
        plan = hd.expand({"equity": 0.5, "cash": 0.5}, 1000.0)
        total = sum(h.notional for h in plan.holdings)
        self.assertAlmostEqual(total, 1000.0, places=6)
        self.assertEqual({h.asset_class for h in plan.holdings}, {"equity", "cash"})

    def test_equities_are_named_with_their_exchange_and_country(self):
        plan = hd.expand({"equity": 1.0}, 800.0)
        self.assertEqual(len(plan.holdings), len(hd.POOLS["equity"]))
        for h in plan.holdings:
            self.assertNotEqual(h.venue, "—")
            self.assertNotEqual(h.country, "—")

    def test_an_unknown_price_is_a_named_gap_not_a_zero(self):
        plan = hd.expand({"equity": 1.0}, 800.0, prices={})
        self.assertTrue(all(h.price is None and h.units is None for h in plan.holdings))
        self.assertTrue(any("قیمت موجود نیست" in g for g in plan.gaps))

    def test_a_known_price_produces_units(self):
        plan = hd.expand({"equity": 0.5, "cash": 0.5}, 1000.0,
                         prices={s: 100.0 for s in hd.POOLS["equity"]})
        eq = [h for h in plan.holdings if h.asset_class == "equity"]
        self.assertTrue(all(h.units is not None for h in eq))
        self.assertAlmostEqual(sum(h.units * 100.0 for h in eq), 500.0, places=6)

    def test_a_negative_price_is_rejected(self):
        plan = hd.expand({"equity": 1.0}, 100.0, prices={"AAPL": -5.0})
        row = [h for h in plan.holdings if h.symbol == "AAPL"][0]
        self.assertIsNone(row.units)
        self.assertTrue(any("نامعتبر" in g for g in plan.gaps))

    def test_the_other_bucket_is_fully_explained(self):
        plan = hd.expand({"other": 0.009, "cash": 0.991}, 100_000.0)
        self.assertEqual(len(plan.other_components), len(hd.OTHER_SPLIT))
        self.assertAlmostEqual(sum(w for _, w, _, _ in plan.other_components), 0.009, places=9)
        self.assertAlmostEqual(sum(m for _, _, m, _ in plan.other_components), 900.0, places=6)

    def test_every_pool_symbol_exists_in_the_catalogue(self):
        from aurora.core import asset_universe as au
        for cls, names in hd.POOLS.items():
            for s in names:
                self.assertTrue(au.exists(s), f"{s} در کاتالوگ نیست")

    def test_explicit_picks_override_the_default_pool(self):
        plan = hd.expand({"equity": 1.0}, 100.0, picks={"equity": ["KO", "JNJ"]})
        self.assertEqual([h.symbol for h in plan.holdings], ["KO", "JNJ"])

    def test_an_empty_portfolio_says_so(self):
        plan = hd.expand({}, 1000.0)
        self.assertEqual(plan.holdings, [])
        self.assertTrue(plan.gaps)

    def test_report_names_symbols_exchanges_and_the_other_split(self):
        plan = hd.expand({"equity": 0.5, "other": 0.009, "cash": 0.491}, 100_000.0)
        text = hd.explain(plan)
        self.assertIn("AAPL", text)
        self.assertIn("XNAS", text)
        self.assertIn("سهم «سایر» شامل چه چیزی است", text)
        self.assertIn("طلا و فلز فیزیکی", text)

    def test_report_never_invents_a_price(self):
        plan = hd.expand({"equity": 1.0}, 1000.0)
        self.assertIn("نامعلوم", hd.explain(plan))
