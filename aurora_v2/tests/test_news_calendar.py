import unittest
from datetime import datetime, timedelta, timezone

from aurora.data import news_calendar as nc

NOW = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Test</title>
<item><title>Fed holds rates</title><link>https://example.org/a</link>
<pubDate>Sat, 14 Nov 2026 09:00:00 GMT</pubDate></item>
<item><title>ECB minutes</title><link>https://example.org/b</link>
<pubDate>Thu, 12 Nov 2026 09:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>T</title>
<entry><title>Atom item</title><link href="https://example.org/c"/>
<published>2026-11-14T08:00:00Z</published></entry></feed>"""


class ParseTests(unittest.TestCase):
    def test_rss_items_are_read_with_dates(self):
        items = nc.parse_feed(RSS, "test")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].title, "Fed holds rates")
        self.assertEqual(items[0].published.tzinfo, timezone.utc)

    def test_atom_links_and_published_dates_are_read(self):
        items = nc.parse_feed(ATOM, "atom")
        self.assertEqual(items[0].link, "https://example.org/c")
        self.assertIsNotNone(items[0].published)

    def test_newest_item_comes_first(self):
        items = nc.parse_feed(RSS)
        self.assertGreater(items[0].published, items[1].published)

    def test_broken_xml_raises_instead_of_silently_returning_nothing(self):
        with self.assertRaises(ValueError):
            nc.parse_feed("<rss><channel>")

    def test_an_empty_feed_is_empty_not_an_error(self):
        self.assertEqual(nc.parse_feed(""), [])

    def test_items_without_a_title_are_skipped(self):
        xml = "<rss><channel><item><link>x</link></item></channel></rss>"
        self.assertEqual(nc.parse_feed(xml), [])


class FetchTests(unittest.TestCase):
    def test_one_dead_feed_does_not_stop_the_others(self):
        def fetcher(url):
            if "dead" in url:
                raise OSError("connection reset")
            return RSS
        results = nc.fetch_feeds(["https://dead.example", "https://live.example"],
                                 fetcher=fetcher, now=NOW)
        self.assertEqual([r.status for r in results], ["error", "ok"])
        self.assertTrue(results[1].items)

    def test_an_empty_feed_is_reported_as_empty(self):
        results = nc.fetch_feeds(["https://e.example"], fetcher=lambda u: "<rss/>", now=NOW)
        self.assertEqual(results[0].status, "empty")

    def test_freshness_is_measured_in_hours(self):
        results = nc.fetch_feeds(["https://live.example"], fetcher=lambda u: RSS, now=NOW)
        self.assertAlmostEqual(results[0].newest_age_hours, 3.0, delta=0.5)

    def test_a_stale_feed_is_named(self):
        old = """<rss><channel><item><title>old</title>
        <pubDate>Mon, 01 Jan 2024 09:00:00 GMT</pubDate></item></channel></rss>"""
        results = nc.fetch_feeds(["https://old.example"], fetcher=lambda u: old, now=NOW)
        self.assertEqual(nc.stale_feeds(results), ["https://old.example"])


class CalendarTests(unittest.TestCase):
    def event(self, hours, impact="high", currency="USD", title="CPI"):
        return nc.Event(NOW + timedelta(hours=hours), title, impact, currency, "US", "test")

    def test_an_imminent_high_impact_event_blocks_new_risk(self):
        allowed, reason = nc.event_risk_gate([self.event(3)], NOW)
        self.assertFalse(allowed)
        self.assertIn("CPI", reason)

    def test_a_distant_event_does_not_block(self):
        allowed, _ = nc.event_risk_gate([self.event(48)], NOW)
        self.assertTrue(allowed)

    def test_a_medium_event_does_not_block_a_high_threshold_gate(self):
        allowed, _ = nc.event_risk_gate([self.event(3, impact="medium")], NOW)
        self.assertTrue(allowed)

    def test_the_window_also_covers_the_minutes_right_after_a_release(self):
        allowed, reason = nc.event_risk_gate([self.event(-1)], NOW)
        self.assertFalse(allowed)
        self.assertIn("از", reason)

    def test_an_event_two_hours_past_no_longer_blocks(self):
        self.assertTrue(nc.event_risk_gate([self.event(-3)], NOW)[0])

    def test_another_currency_is_ignored_when_usd_is_tracked(self):
        allowed, _ = nc.event_risk_gate([self.event(2, currency="EUR")], NOW)
        self.assertTrue(allowed)

    def test_an_empty_calendar_is_reported_as_no_known_event(self):
        allowed, reason = nc.event_risk_gate([], NOW)
        self.assertTrue(allowed)
        self.assertIn("نیست", reason)

    def test_a_row_without_a_timezone_is_refused(self):
        with self.assertRaises(ValueError):
            nc.parse_event_row({"when": "2026-11-14T10:00:00", "title": "CPI", "impact": "high"})

    def test_an_unknown_impact_level_is_refused(self):
        with self.assertRaises(ValueError):
            nc.parse_event_row({"when": "2026-11-14T10:00:00+00:00",
                                "title": "CPI", "impact": "extreme"})

    def test_a_row_without_a_title_is_refused(self):
        with self.assertRaises(ValueError):
            nc.parse_event_row({"when": "2026-11-14T10:00:00+00:00", "impact": "high"})

    def test_upcoming_returns_only_the_window(self):
        events = [self.event(2), self.event(70)]
        self.assertEqual(len(nc.upcoming(events, NOW, hours=24)), 1)

    def test_a_missing_calendar_file_is_reported_not_assumed(self):
        events, problems = nc.load_calendar("/tmp/does-not-exist-aurora.csv")
        self.assertEqual(events, [])
        self.assertTrue(problems)


if __name__ == "__main__":
    unittest.main()
