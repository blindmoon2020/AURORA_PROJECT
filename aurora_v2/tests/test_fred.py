import os
import unittest

from aurora.data import fred

PAYLOAD = {
    "observations": [
        {"date": "2026-11-09", "value": "4.88"},
        {"date": "2026-11-06", "value": "4.75"},
        {"date": "2026-11-08", "value": "."},
        {"date": "2026-11-07", "value": ""},
        {"date": "2026-11-05"},
    ]
}


class ParseTests(unittest.TestCase):
    def test_missing_values_are_skipped_not_zero_filled(self):
        pts = fred.parse_observations(PAYLOAD)
        self.assertEqual([p.date for p in pts], ["2026-11-06", "2026-11-09"])
        self.assertNotIn(0.0, [p.value for p in pts])

    def test_sorted_ascending(self):
        pts = fred.parse_observations(PAYLOAD)
        self.assertEqual(pts, sorted(pts, key=lambda p: p.date))

    def test_empty_payload(self):
        self.assertEqual(fred.parse_observations({}), [])


class RegistryTests(unittest.TestCase):
    def test_every_series_documents_its_lag(self):
        for sid, meta in fred.MACRO_SERIES.items():
            self.assertIn("lag_days", meta, sid)
            self.assertGreaterEqual(meta["lag_days"], 1, sid)
            self.assertIn("unit", meta, sid)

    def test_curve_series_present(self):
        for sid in ("DGS10", "DGS2", "T10Y2Y", "VIXCLS", "BAMLH0A0HYM2"):
            self.assertIn(sid, fred.MACRO_SERIES)


class KeyTests(unittest.TestCase):
    def test_missing_key_is_a_clear_error(self):
        saved = os.environ.pop("FRED_API_KEY", None)
        try:
            with self.assertRaises(fred.FredError):
                fred.fetch_series("DGS10", cache_dir="/tmp/fred_test_nokey")
        finally:
            if saved:
                os.environ["FRED_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
