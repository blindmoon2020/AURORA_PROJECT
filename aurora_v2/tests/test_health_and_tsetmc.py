import tempfile
import unittest
from pathlib import Path

from aurora.health import cache_age_days, source_rows, verdict
from aurora.tsetmc import TsetmcSymbolError, load_tsetmc_listing, normalize_persian, resolve_tsetmc

LISTING = {"IRO1FOLD0001": {"isin": "IRO1FOLD0001", "ticker": "فولاد",
                            "name": "فولاد مبارکه اصفهان"}}


class PersianTests(unittest.TestCase):
    def test_arabic_letters_are_folded(self):
        self.assertEqual(normalize_persian("فولاد"), normalize_persian("فولاد"))
        self.assertEqual(normalize_persian("كريم"), normalize_persian("کریم"))

    def test_zwnj_and_digits_are_handled(self):
        self.assertEqual(normalize_persian("مبارکه\u200cای"), "مبارکه ای")
        self.assertEqual(normalize_persian("۱۲۳"), "123")

    def test_resolve_by_isin_ticker_and_name(self):
        self.assertEqual(resolve_tsetmc("IRO1FOLD0001", LISTING)["ticker"], "فولاد")
        self.assertEqual(resolve_tsetmc("فولاد", LISTING)["isin"], "IRO1FOLD0001")
        self.assertEqual(resolve_tsetmc("فولاد مبارکه اصفهان", LISTING)["ticker"], "فولاد")

    def test_partial_name_is_a_suggestion_not_a_guess(self):
        with self.assertRaises(TsetmcSymbolError) as ctx:
            resolve_tsetmc("فولاد مبارک", LISTING)
        self.assertTrue(ctx.exception.candidates)


class HealthTests(unittest.TestCase):
    def test_missing_key_is_distinct_from_missing_cache(self):
        with tempfile.TemporaryDirectory() as d:
            rows = {r["source"]: r for r in source_rows(Path(d), env={"FRED_API_KEY": "x"})}
            self.assertEqual(rows["finnhub"]["status"], "no credential")
            self.assertEqual(rows["fred"]["status"], "no cache")
            self.assertEqual(rows["yahoo"]["status"], "no cache")

    def test_stale_cache_is_reported_with_its_age(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "EURUSD_1d.json"
            f.write_text("{}")
            age = cache_age_days(Path(d), "*_1d.json", now=f.stat().st_mtime + 10 * 86400)
            self.assertAlmostEqual(age, 10.0, places=3)
            rows = {r["source"]: r for r in source_rows(
                Path(d), env={"TWELVEDATA_API_KEY": "k"}, now=f.stat().st_mtime + 10 * 86400)}
            self.assertEqual(rows["twelvedata"]["status"], "stale")

    def test_verdict_names_the_blocking_sources(self):
        rows = [{"source": "a", "status": "ok"}, {"source": "b", "status": "no credential"},
                {"source": "c", "status": "stale"}]
        usable, degraded, blocked = verdict(rows)
        self.assertEqual((usable, degraded, blocked), (1, 1, ["b"]))


if __name__ == "__main__":
    unittest.main()
