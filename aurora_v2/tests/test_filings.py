import datetime as dt
import unittest

from aurora.data.filings import (STALE_DAYS, age_days, freshness, guard_no_lookahead,
                                 is_stale, public_at)


def ts(day):
    return int(dt.datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


ROWS = [{"filing_date": "2019-03-01", "eps": 1.0},
        {"filing_date": "2020-03-01", "eps": 1.2},
        {"filing_date": "2021-03-01", "eps": 1.5}]


class PointInTimeTests(unittest.TestCase):
    def test_future_filings_never_qualify(self):
        row = public_at(ROWS, ts("2020-06-01"))
        self.assertEqual(row["eps"], 1.2)

    def test_no_filing_yet_returns_nothing(self):
        self.assertIsNone(public_at(ROWS, ts("2018-01-01")))

    def test_same_day_filing_is_usable(self):
        self.assertEqual(public_at(ROWS, ts("2020-03-01"))["eps"], 1.2)


class FreshnessTests(unittest.TestCase):
    def test_age_in_days(self):
        self.assertAlmostEqual(age_days(ROWS[2], ts("2021-04-01")), 31.0, places=3)

    def test_old_filing_is_stale(self):
        self.assertTrue(is_stale(ROWS[0], ts("2026-11-14")))
        self.assertFalse(is_stale(ROWS[0], ts("2019-06-01")))

    def test_missing_filing_counts_as_stale(self):
        self.assertTrue(is_stale(None, ts("2026-11-14")))

    def test_stale_threshold_is_over_a_year(self):
        self.assertGreater(STALE_DAYS, 400)

    def test_freshness_summary_names_the_stale_names(self):
        # the median must describe the book, not be dragged by one dead name
        f = freshness({"OLD": [ROWS[0]],
                       "A": [{"filing_date": "2026-06-01", "eps": 2.0}],
                       "B": [{"filing_date": "2026-08-01", "eps": 2.1}],
                       "C": [{"filing_date": "2026-09-01", "eps": 2.2}]},
                      ts("2026-11-14"))
        self.assertEqual(f.stale, ["OLD"])
        self.assertIn("OLD", f.summary())
        self.assertLess(f.median_age_days, 400)


class LookaheadGuardTests(unittest.TestCase):
    def test_clean_set_passes(self):
        guard_no_lookahead([ROWS[0], ROWS[1]], ts("2020-06-01"))

    def test_future_row_raises(self):
        with self.assertRaises(ValueError):
            guard_no_lookahead(ROWS, ts("2020-06-01"))

    def test_missing_date_raises_because_it_cannot_be_proved(self):
        with self.assertRaises(ValueError):
            guard_no_lookahead([{"eps": 1.0}], ts("2020-06-01"))


if __name__ == "__main__":
    unittest.main()
