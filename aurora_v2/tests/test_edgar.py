import unittest
from unittest import mock

from aurora.data import edgar

PAYLOAD = {"units": {"USD/shares": [
    {"end": "2025-09-27", "filed": "2025-10-31", "val": 6.1},
    {"end": "2024-09-28", "filed": "2024-11-01", "val": 5.8},
    {"end": "2023-09-30", "filed": None, "val": 9.9},
]}}


class EdgarTests(unittest.TestCase):
    def test_missing_cik_is_named(self):
        with mock.patch.object(edgar, "cik_map", return_value={"MSFT": "0000789019"}):
            with self.assertRaises(edgar.EdgarError) as ctx:
                edgar.eps_points("NOTREAL")
        self.assertIn("no CIK", str(ctx.exception))

    def test_facts_without_a_filing_date_are_dropped(self):
        with mock.patch.object(edgar, "cik_map", return_value={"AAPL": "0000320193"}), \
             mock.patch.object(edgar, "_get", return_value=PAYLOAD):
            points = edgar.eps_points("AAPL")
        self.assertEqual(len(points), 2)
        self.assertEqual([p["eps"] for p in points], [5.8, 6.1])
        self.assertTrue(all(p["filed"] for p in points))

    def test_no_usable_facts_raises(self):
        with mock.patch.object(edgar, "cik_map", return_value={"AAPL": "0000320193"}), \
             mock.patch.object(edgar, "_get", return_value={"units": {}}):
            with self.assertRaises(edgar.EdgarError):
                edgar.eps_points("AAPL")
