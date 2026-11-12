import os
import unittest
from unittest import mock

from aurora.core.types import Candle
from aurora.data import twelvedata as td


class ParseTests(unittest.TestCase):
    def test_parses_and_sorts_oldest_first(self):
        payload = {"values": [
            {"datetime": "2026-11-11 09:00:00", "open": "1.1010", "high": "1.1020",
             "low": "1.1000", "close": "1.1015", "volume": "0"},
            {"datetime": "2026-11-11 08:00:00", "open": "1.1000", "high": "1.1015",
             "low": "1.0990", "close": "1.1010", "volume": "1234"},
        ]}
        candles = td.parse_time_series(payload)
        self.assertEqual(len(candles), 2)
        self.assertLess(candles[0].ts, candles[1].ts)
        self.assertEqual(candles[1].close, 1.1015)
        self.assertEqual(candles[0].volume, 1234.0)   # kept from equities/crypto
        self.assertEqual(candles[1].volume, 0.0)      # spot FX has none, not invented

    def test_daily_rows_without_time(self):
        payload = {"values": [
            {"datetime": "2026-11-10", "open": "1.1", "high": "1.2", "low": "1.0", "close": "1.15"},
        ]}
        candles = td.parse_time_series(payload)
        self.assertEqual(len(candles), 1)
        self.assertEqual(candles[0].volume, 0.0)

    def test_error_payload_raises(self):
        with self.assertRaises(td.TwelveDataError):
            td.parse_time_series({"code": 429, "message": "API limit reached", "status": "error"})
        with self.assertRaises(td.TwelveDataError):
            td.parse_time_series({"values": [{"datetime": "nope", "open": 1}]})
        with self.assertRaises(td.TwelveDataError):
            td.parse_time_series({"unexpected": True})

    def test_bad_interval_rejected_before_network(self):
        with self.assertRaises(td.TwelveDataError):
            td.fetch_time_series("EUR/USD", "3m", use_cache=False)

    def test_missing_key_is_a_clear_error(self):
        with mock.patch.dict(os.environ, {"TWELVEDATA_API_KEY": ""}, clear=False):
            with self.assertRaises(td.TwelveDataError) as ctx:
                td.fetch_time_series("EUR/USD", "1h", use_cache=False)
        self.assertIn("TWELVEDATA_API_KEY", str(ctx.exception))

    def test_interval_map_covers_daily(self):
        self.assertEqual(td.INTERVALS["1d"], "1day")
        self.assertEqual(td.INTERVALS["1h"], "1h")


if __name__ == "__main__":
    unittest.main()
