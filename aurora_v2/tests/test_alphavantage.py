import unittest

from aurora.data import alphavantage as av

DAILY = {"Meta Data": {"2. Symbol": "AAPL"},
         "Time Series (Daily)": {
             "2026-11-10": {"1. open": "348.00", "2. high": "352.00",
                            "3. low": "347.10", "4. close": "351.20", "5. volume": "41000000"},
             "2026-11-11": {"1. open": "350.00", "2. high": "358.00",
                            "3. low": "349.10", "4. close": "355.63", "5. volume": "34284700"},
         }}

OVERVIEW = {"Symbol": "AAPL", "Name": "Apple Inc", "Sector": "TECHNOLOGY",
            "Industry": "Electronic Computers", "Currency": "USD", "Exchange": "NASDAQ",
            "PERatio": "38.9", "PriceToBookRatio": "44.06", "ROE": "1.2761",
            "Beta": "1.09", "DividendYield": "None", "MarketCapitalization": "5200000000000"}


class DailyParsingTests(unittest.TestCase):
    def test_rows_are_sorted_oldest_first(self):
        candles = av.parse_daily(DAILY, "AAPL")
        self.assertEqual(len(candles), 2)
        self.assertLess(candles[0].ts, candles[1].ts)
        self.assertAlmostEqual(candles[1].close, 355.63)
        self.assertAlmostEqual(candles[1].volume, 34_284_700)

    def test_missing_series_raises(self):
        with self.assertRaises(av.AlphaVantageError):
            av.parse_daily({"Note": "slow down"}, "AAPL")

    def test_malformed_row_raises_with_symbol(self):
        broken = {"Time Series (Daily)": {"2026-11-11": {"1. open": "not a number"}}}
        with self.assertRaises(av.AlphaVantageError):
            av.parse_daily(broken, "AAPL")


class OverviewParsingTests(unittest.TestCase):
    def test_fields_are_typed_and_missing_becomes_none(self):
        ov = av.parse_overview(OVERVIEW)
        self.assertEqual(ov["symbol"], "AAPL")
        self.assertAlmostEqual(ov["pe_ratio"], 38.9)
        self.assertAlmostEqual(ov["roe"], 1.2761)
        self.assertIsNone(ov["dividend_yield"], "a 'None' string must not become 0.0")

    def test_overview_without_symbol_raises(self):
        with self.assertRaises(av.AlphaVantageError):
            av.parse_overview({"Information": "premium endpoint"})


class RateLimitTests(unittest.TestCase):
    def test_provider_notice_is_an_error_not_an_empty_list(self):
        with self.assertRaises(av.AlphaVantageError):
            av.parse_daily({"Information": "premium endpoint"}, "AAPL")


if __name__ == "__main__":
    unittest.main()
