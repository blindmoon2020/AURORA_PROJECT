import unittest

from aurora.data import eodhd


def row(date="2026-01-05", close=100.0, adj=50.0):
    return {"date": date, "open": 98.0, "high": 102.0, "low": 97.0,
            "close": close, "adjusted_close": adj, "volume": 1000}


class NormaliseTests(unittest.TestCase):
    def test_bare_ticker_defaults_to_us(self):
        self.assertEqual(eodhd.normalise("aapl"), "AAPL.US")

    def test_exchange_is_honoured(self):
        self.assertEqual(eodhd.normalise("spy", "lse"), "SPY.LSE")

    def test_suffixed_ticker_is_left_alone(self):
        self.assertEqual(eodhd.normalise("EURUSD.FOREX"), "EURUSD.FOREX")


class ParseTests(unittest.TestCase):
    def test_split_adjustment_scales_the_whole_bar(self):
        c = eodhd.parse_eod([row()])[0]
        self.assertEqual(c.close, 50.0)
        self.assertGreaterEqual(c.high, c.close)   # the bar stays coherent
        self.assertGreaterEqual(c.close, c.low)
        self.assertAlmostEqual(c.open, 49.0)

    def test_missing_adjusted_close_falls_back_to_raw(self):
        r = row()
        r.pop("adjusted_close")
        self.assertEqual(eodhd.parse_eod([r])[0].close, 100.0)

    def test_error_payload_as_dict_raises(self):
        with self.assertRaises(eodhd.EODHDError):
            eodhd.parse_eod({"error": "Invalid API token"})

    def test_error_payload_as_text_list_raises(self):
        with self.assertRaises(eodhd.EODHDError):
            eodhd.parse_eod(["Ticker Not Found."])

    def test_malformed_row_raises_instead_of_being_skipped(self):
        bad = [{"date": "2026-01-05", "open": 1, "high": 1, "low": 1}]
        with self.assertRaises(eodhd.EODHDError):
            eodhd.parse_eod(bad)

    def test_rows_are_sorted_by_time(self):
        out = eodhd.parse_eod([row("2026-01-07"), row("2026-01-06")])
        self.assertLess(out[0].ts, out[1].ts)


class CoverageTests(unittest.TestCase):
    def test_reports_depth_so_a_short_history_is_visible(self):
        out = eodhd.parse_eod([row("2025-11-12"), row("2026-11-11")])
        cov = eodhd.coverage(out)
        self.assertEqual(cov["bars"], 2)
        self.assertAlmostEqual(cov["years"], 1.0, places=1)

    def test_empty_series_is_zero_not_an_error(self):
        self.assertEqual(eodhd.coverage([]), {"bars": 0, "years": 0.0})
