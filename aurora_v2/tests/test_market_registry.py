import unittest

from aurora.core import market_registry as mr


class RegistryTests(unittest.TestCase):
    def test_the_registry_has_no_structural_problems(self):
        self.assertEqual(mr.audit(), [])

    def test_every_continent_has_at_least_one_venue(self):
        for continent in mr.CONTINENTS:
            self.assertTrue(mr.venues_in(continent), continent)

    def test_the_countries_the_owner_named_are_registered(self):
        countries = mr.country_venues()
        for code in ("IN", "CA", "FR", "DE", "JP", "US"):
            self.assertIn(code, countries, code)

    def test_african_exchanges_are_present(self):
        african = {e.country for e in mr.venues_in(mr.AFRICA)}
        self.assertGreaterEqual(len(african), 4)

    def test_a_local_ticker_gets_its_provider_suffix(self):
        self.assertEqual(mr.provider_symbol("RELIANCE", "XNSE"), "RELIANCE.NS")
        self.assertEqual(mr.provider_symbol("RY", "XTSX"), "RY.TO")
        self.assertEqual(mr.provider_symbol("SAP", "XETR"), "SAP.DE")
        self.assertEqual(mr.provider_symbol("AAPL", "XNAS"), "AAPL")

    def test_an_unknown_venue_raises_instead_of_guessing_a_suffix(self):
        with self.assertRaises(mr.UnknownVenue):
            mr.provider_symbol("XYZ", "NOPE")

    def test_an_empty_ticker_is_refused(self):
        with self.assertRaises(ValueError):
            mr.provider_symbol("  ", "XNSE")

    def test_the_symbols_the_owner_named_as_indices_exist(self):
        for symbol in ("^NDX", "^DJI", "^N225", "^GDAXI", "^BSESN", "^NSEI"):
            self.assertEqual(mr.index_symbol(symbol).symbol, symbol)

    def test_every_index_points_at_a_registered_venue(self):
        for idx in mr.INDICES:
            self.assertIn(idx.venue, mr.EXCHANGES, idx.symbol)

    def test_coverage_reports_countries_and_continents_not_vibes(self):
        c = mr.coverage()
        self.assertGreaterEqual(c["countries"], 30)
        self.assertEqual(sum(c["continents"].values()), c["venues"])
        self.assertGreaterEqual(c["indices"], 25)

    def test_veneer_gaps_are_named_per_venue(self):
        c = mr.coverage()
        self.assertTrue(c["venues_with_free_feed_gap"], "شکاف داده باید نام‌گذاری شود")

    def test_iran_has_an_index_registered(self):
        self.assertTrue(mr.indices_for("IR"))

    def test_country_venues_are_sorted_and_complete(self):
        mapping = mr.country_venues()
        self.assertEqual(len(mapping), len({ex.country for ex in mr.EXCHANGES.values()}))


if __name__ == "__main__":
    unittest.main()
