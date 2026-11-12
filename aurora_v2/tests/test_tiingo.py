import json
import os
import unittest
import urllib.error
from unittest import mock

from aurora.data import tiingo

ROWS = [
    {"date": "2026-11-11T00:00:00.000Z", "open": 97.0, "high": 98.0,
     "low": 96.5, "close": 97.57, "volume": 1000, "adjClose": 97.57},
    {"date": "2025-01-02T00:00:00.000Z", "open": 62.0, "high": 62.5,
     "low": 61.5, "close": 61.84, "volume": 2000, "adjClose": 58.9091},
]


class ParseTests(unittest.TestCase):
    def test_sorts_ascending_and_parses_utc(self):
        candles = tiingo.parse_rows(list(reversed(ROWS)))
        self.assertLess(candles[0].ts, candles[1].ts)
        self.assertEqual(candles[0].ts % 86400, 0)     # midnight UTC, no timezone drift

    def test_adjustment_scales_every_price_field(self):
        candles = tiingo.parse_rows(ROWS, adjusted=True)
        old = candles[0]
        factor = 58.9091 / 61.84
        self.assertAlmostEqual(old.close, 61.84 * factor, places=9)
        self.assertAlmostEqual(old.open, 62.0 * factor, places=9)
        self.assertAlmostEqual(old.high, 62.5 * factor, places=9)
        self.assertAlmostEqual(old.low, 61.5 * factor, places=9)
        self.assertLess(old.close, 61.84)              # a dividend payer's history is lowered

    def test_raw_mode_keeps_printed_prices(self):
        candles = tiingo.parse_rows(ROWS, adjusted=False)
        self.assertAlmostEqual(candles[0].close, 61.84, places=9)

    def test_most_recent_bar_is_not_rescaled(self):
        candles = tiingo.parse_rows(ROWS, adjusted=True)
        self.assertAlmostEqual(candles[-1].close, 97.57, places=9)

    def test_missing_adjclose_means_no_adjustment(self):
        row = dict(ROWS[0])
        row.pop("adjClose")
        self.assertAlmostEqual(tiingo.parse_rows([row])[0].close, row["close"], places=9)

    def test_zero_close_does_not_divide_by_zero(self):
        row = {"date": "2026-11-11T00:00:00.000Z", "open": 0.0, "high": 0.0,
               "low": 0.0, "close": 0.0, "volume": 0, "adjClose": 0.0}
        candles = tiingo.parse_rows([row])
        self.assertEqual(candles[0].close, 0.0)


class ErrorTests(unittest.TestCase):
    def test_missing_key_raises(self):
        with mock.patch.dict(os.environ, {"TIINGO_API_KEY": ""}, clear=False):
            with self.assertRaises(tiingo.TiingoError):
                tiingo._key()

    def test_forbidden_is_named_not_swallowed(self):
        err = urllib.error.HTTPError("u", 403, "Forbidden", {}, None)
        err.read = lambda: b'{"detail":"You do not have permission"}'
        with mock.patch.object(tiingo, "_key", return_value="k"), \
             mock.patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(tiingo.TiingoError) as ctx:
                tiingo._get("news", {})
        self.assertIn("permission", str(ctx.exception))

    def test_metadata_payload_is_not_mistaken_for_prices(self):
        with mock.patch.object(tiingo, "_cached", return_value={"ticker": "AAPL"}):
            with self.assertRaises(tiingo.TiingoError):
                tiingo.fetch_daily("AAPL")


if __name__ == "__main__":
    unittest.main()
