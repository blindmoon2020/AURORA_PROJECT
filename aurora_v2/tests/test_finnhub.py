import os
import unittest
from unittest import mock

from aurora.data import finnhub

QUOTE = {"c": 355.63, "d": 7.12, "dp": 2.043, "h": 357.0, "l": 349.1,
         "o": 350.0, "pc": 348.51, "t": 1794400000}
UNKNOWN = {"c": 0.0, "d": 0.0, "dp": 0.0, "h": 0.0, "l": 0.0, "o": 0.0, "pc": 0.0, "t": 0}
PROFILE = {"name": "Apple Inc.", "finnhubIndustry": "Technology",
           "marketCapitalization": 3480000.0, "currency": "USD", "exchange": "NASDAQ"}
METRIC = {"metric": {"peTTM": 38.9, "pbAnnual": 44.06, "roeTTM": "127.61",
                     "beta": 1.09, "52WeekHigh": 366.0, "52WeekLow": 240.1,
                     "peForward": 31.0}}


class ParseTests(unittest.TestCase):
    def test_quote(self):
        q = finnhub.parse_quote("AAPL", QUOTE)
        self.assertEqual(q.price, 355.63)
        self.assertAlmostEqual(q.change_pct, 2.043)
        self.assertEqual(q.prev_close, 348.51)

    def test_unknown_symbol_is_none_not_zero(self):
        q = finnhub.parse_quote("NOPE", UNKNOWN)
        self.assertIsNone(q.price)

    def test_profile(self):
        p = finnhub.parse_profile("AAPL", PROFILE)
        self.assertEqual(p.name, "Apple Inc.")
        self.assertEqual(p.industry, "Technology")
        self.assertEqual(p.market_cap_musd, 3480000.0)

    def test_missing_market_cap_is_none(self):
        p = finnhub.parse_profile("X", {"name": "X"})
        self.assertIsNone(p.market_cap_musd)

    def test_metrics_map_and_strings_are_numbers(self):
        f = finnhub.parse_fundamentals("AAPL", METRIC)
        self.assertAlmostEqual(f.pe_ttm, 38.9)
        self.assertAlmostEqual(f.roe_ttm, 127.61)     # arrived as a string
        self.assertAlmostEqual(f.beta, 1.09)
        self.assertIsNone(f.ps_ttm)                   # absent, not zero

    def test_empty_metric_block(self):
        f = finnhub.parse_fundamentals("X", {})
        self.assertIsNone(f.pe_ttm)

    def test_missing_key_raises_clearly(self):
        with mock.patch.dict(os.environ, {"FINNHUB_API_KEY": ""}, clear=False):
            with self.assertRaises(finnhub.FinnhubError):
                finnhub._key()


if __name__ == "__main__":
    unittest.main()
