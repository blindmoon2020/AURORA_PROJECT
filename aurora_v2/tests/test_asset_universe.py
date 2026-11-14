import unittest

from aurora.core import asset_universe as au


class ExpansionTests(unittest.TestCase):
    """The owner's requirement: all FX pairs, all metals, all agri, many ETFs and funds, and
    bonds of the US and other countries - not a token sample of each."""

    def test_all_world_fx_pairs_are_present(self):
        from aurora.core import asset_universe as au
        pairs = {i.symbol for i in au.by_class(au.FX)}
        self.assertGreaterEqual(len(pairs), 60)
        for required in ("EURUSD", "USDJPY", "EURGBP", "USDCNH", "USDINR", "USDZAR",
                         "USDBRL", "USDTRY", "USDIRR"):
            self.assertIn(required, pairs)

    def test_metals_cover_precious_and_industrial(self):
        from aurora.core import asset_universe as au
        metals = {i.symbol for i in au.by_class(au.METALS)}
        for required in ("XAUUSD", "XAGUSD", "GC=F", "SI=F", "HG=F", "LME_NI", "LME_ZN"):
            self.assertIn(required, metals)

    def test_agriculture_includes_the_iranian_commodities(self):
        from aurora.core import asset_universe as au
        agri = {i.symbol for i in au.by_class(au.AGRI)}
        for required in ("ZC=F", "ZW=F", "KC=F", "SB=F", "CC=F", "CT=F",
                         "زعفران_نگین", "پسته"):
            self.assertIn(required, agri)

    def test_funds_and_etfs_are_not_a_token_list(self):
        from aurora.core import asset_universe as au
        self.assertGreaterEqual(len(au.by_class(au.ETF)), 50)
        self.assertGreaterEqual(len(au.by_class(au.FUND)), 6)

    def test_bonds_cover_the_us_and_other_countries(self):
        from aurora.core import asset_universe as au
        bonds = {i.symbol for i in au.by_class(au.FIXED_INCOME)}
        for required in ("ZN=F", "ZB=F", "FBTP", "JBTP", "اخزا"):
            self.assertIn(required, bonds)

    def test_the_catalogue_stays_structurally_sound_at_this_size(self):
        from aurora.core import asset_universe as au
        self.assertEqual(au.audit(), [])
        self.assertGreaterEqual(len(au.INSTRUMENTS), 240)

    def test_no_symbol_is_duplicated(self):
        from aurora.core import asset_universe as au
        symbols = [i.symbol for i in au.INSTRUMENTS]
        self.assertEqual(len(symbols), len(set(symbols)))


class CatalogueTests(unittest.TestCase):
    def test_the_catalogue_has_no_structural_problems(self):
        self.assertEqual(au.audit(), [])

    def test_an_unknown_symbol_raises_instead_of_guessing(self):
        with self.assertRaises(au.UnknownInstrument):
            au.get("NOT-A-SYMBOL")
        self.assertFalse(au.exists("NOT-A-SYMBOL"))

    def test_every_asset_class_the_owner_named_is_represented(self):
        from aurora.core.asset_universe import ASSET_CLASSES
        counts = {c: len(au.by_class(c)) for c in ASSET_CLASSES}
        empty = [c for c, n in counts.items() if n == 0]
        self.assertEqual(empty, [], f"کلاس بدون ابزار: {empty}")

    def test_agricultural_commodities_are_covered(self):
        symbols = {i.symbol for i in au.by_class(au.AGRI)}
        for expected in ("ZC", "ZW", "KC"):
            self.assertIn(expected, symbols)

    def test_iranian_market_instruments_exist(self):
        symbols = {i.symbol for i in au.by_venue("XTSE_IR")}
        self.assertTrue(symbols)
        self.assertIn("زعفران_نگین", {i.symbol for i in au.by_venue("IME_IR")})

    def test_energy_and_metals_are_separated_from_equity(self):
        self.assertEqual(au.get("CL").asset_class, au.ENERGY)
        self.assertEqual(au.get("GC").asset_class, au.METALS)
        self.assertEqual(au.get("SPY").asset_class, au.ETF)

    def test_fx_majors_carry_their_real_contract_size(self):
        self.assertEqual(au.get("EURUSD").size, 100000)

    def test_nft_and_metaverse_are_declared_but_unverified(self):
        for symbol in ("NFT-BAYC", "SAND-USD"):
            self.assertFalse(au.get(symbol).verified,
                             "ابزاری که داده نهادی ندارد نباید تأییدشده علامت بخورد")

    def test_contract_value_uses_the_contract_size(self):
        self.assertEqual(au.contract_value("GC", 2400), 240000)
        self.assertEqual(au.contract_value("AAPL", 200), 200)

    def test_contract_value_rejects_a_nonsense_price(self):
        with self.assertRaises(ValueError):
            au.contract_value("AAPL", 0)

    def test_coverage_reports_verified_and_assumed_separately(self):
        c = au.coverage()
        self.assertEqual(c["verified"] + c["unverified"], c["instruments"])
        self.assertEqual(c["classes_missing"], [])
        self.assertGreater(c["unverified"], 0, "صداقت یعنی فرض‌ها پنهان نشوند")

    def test_search_finds_a_symbol_and_a_persian_name(self):
        self.assertTrue(any(i.symbol == "KC" for i in au.search("KC")))
        self.assertTrue(any(i.symbol == "زعفران_نگین" for i in au.search("زعفران")))

    def test_every_venue_declares_hours_settlement_and_currency(self):
        for code, v in au.VENUES.items():
            self.assertTrue(v.open_local and v.close_local, code)
            self.assertTrue(v.settlement, code)
            self.assertTrue(v.currency, code)
            self.assertTrue(v.days, code)

    def test_a_tehran_venue_knows_its_week_is_not_monday_to_friday(self):
        self.assertEqual(au.venue("XTSE_IR").days, "Sat-Wed")

    def test_crypto_is_declared_as_trading_continuously(self):
        self.assertEqual(au.venue("XCRYPTO").days, "24/7")


if __name__ == "__main__":
    unittest.main()
