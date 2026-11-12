import io
import json
import os
import unittest
import urllib.error
from unittest import mock

from aurora.data import fmp

PROFILE = [{
    "symbol": "MSFT", "companyName": "Microsoft Corporation", "sector": "Technology",
    "industry": "Software - Infrastructure", "marketCap": 3869973263750,
    "beta": 1.044, "price": 521.125,
}]
INCOME = [{
    "date": "2026-06-30", "symbol": "MSFT", "revenue": 331839000000,
    "netIncome": 133749000000, "filingDate": "2026-07-29",
}]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(payload):
    def _open(url, timeout=30):
        return FakeResponse(json.dumps(payload).encode())
    return _open


class SnapshotTests(unittest.TestCase):
    def test_snapshot_carries_the_filing_date(self):
        with mock.patch.object(fmp, "profile", return_value=PROFILE[0]), \
             mock.patch.object(fmp, "income_statement", return_value=INCOME):
            snap = fmp.snapshot("MSFT")
        self.assertEqual(snap.sector, "Technology")
        self.assertEqual(snap.period_end, "2026-06-30")
        self.assertEqual(snap.filing_date, "2026-07-29")
        # usable only from the filing date, never from the period end
        self.assertGreater(snap.available_from_ts, 1780000000)

    def test_no_dates_means_unusable_not_zero(self):
        with mock.patch.object(fmp, "profile", return_value={"companyName": "X"}), \
             mock.patch.object(fmp, "income_statement", return_value=[{}]):
            snap = fmp.snapshot("X")
        self.assertIsNone(snap.available_from_ts)
        self.assertIsNone(snap.revenue)

    def test_missing_numbers_stay_none(self):
        with mock.patch.object(fmp, "profile", return_value={"companyName": "X", "beta": None}), \
             mock.patch.object(fmp, "income_statement", return_value=[]):
            snap = fmp.snapshot("X")
        self.assertIsNone(snap.beta)
        self.assertEqual(snap.revenue, None)


class ErrorMappingTests(unittest.TestCase):
    def _raise(self, code):
        err = urllib.error.HTTPError("u", code, "x", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=err):
            return fmp._get("income-statement", {"symbol": "AAPL"})

    def test_paid_endpoint_is_named(self):
        with self.assertRaises(fmp.FmpError) as ctx:
            self._raise(402)
        self.assertIn("paid plan", str(ctx.exception))

    def test_bad_key_is_named(self):
        with self.assertRaises(fmp.FmpError) as ctx:
            self._raise(403)
        self.assertIn("FMP_API_KEY", str(ctx.exception))

    def test_rate_limit_is_named(self):
        with self.assertRaises(fmp.FmpError) as ctx:
            self._raise(429)
        self.assertIn("rate limit", str(ctx.exception))

    def test_missing_key_raises(self):
        with mock.patch.dict(os.environ, {"FMP_API_KEY": ""}, clear=False):
            with self.assertRaises(fmp.FmpError):
                fmp._key()


class CacheTests(unittest.TestCase):
    def test_empty_answer_is_not_cached_but_data_is(self):
        import tempfile
        from pathlib import Path
        calls = {"empty": 0, "data": 0}

        def empty():
            calls["empty"] += 1
            return []

        def data():
            calls["data"] += 1
            return [{"symbol": "AAPL"}]

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(fmp, "CACHE", Path(tmp)):
                self.assertEqual(fmp._cached("e", empty), [])
                self.assertEqual(fmp._cached("e", empty), [])
                self.assertEqual(calls["empty"], 2)      # a miss must not be frozen in place
                self.assertEqual(fmp._cached("d", data), [{"symbol": "AAPL"}])
                self.assertEqual(fmp._cached("d", data), [{"symbol": "AAPL"}])
                self.assertEqual(calls["data"], 1)       # real data is cached
