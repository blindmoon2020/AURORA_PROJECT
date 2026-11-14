import datetime as dt
import unittest

from aurora.core.types import Candle
from aurora.execution.paper_book import PaperBook, Position, apply_fills
from aurora.market_calendar import (ET, fill_is_next_open, is_open, is_trading_day,
                                    next_session_open)


def ts(y, m, d, h=0, mi=0):
    return dt.datetime(y, m, d, h, mi, tzinfo=ET).timestamp()


class CalendarTests(unittest.TestCase):
    def test_weekend_is_closed(self):
        self.assertFalse(is_trading_day("2026-11-14"))     # Saturday
        self.assertFalse(is_trading_day("2026-11-15"))     # Sunday

    def test_regular_session_hours(self):
        self.assertTrue(is_open(ts(2026, 11, 13, 10, 0)))
        self.assertFalse(is_open(ts(2026, 11, 13, 9, 0)))
        self.assertFalse(is_open(ts(2026, 11, 13, 16, 30)))

    def test_thanksgiving_is_closed(self):
        self.assertFalse(is_trading_day("2026-11-26"))
        self.assertTrue(is_trading_day("2026-11-27"))

    def test_next_open_skips_the_weekend_and_the_holiday(self):
        fri = ts(2026, 11, 13, 16, 30)
        nxt = next_session_open(fri)
        self.assertEqual(dt.datetime.fromtimestamp(nxt, tz=ET).date(), dt.date(2026, 11, 16))
        wed_before = ts(2026, 11, 25, 16, 30)
        nxt2 = next_session_open(wed_before)
        self.assertEqual(dt.datetime.fromtimestamp(nxt2, tz=ET).date(), dt.date(2026, 11, 27))

    def test_fill_must_be_the_verys_next_open(self):
        fri_close = ts(2026, 11, 13, 16, 30)
        monday_open = next_session_open(fri_close)
        self.assertTrue(fill_is_next_open(fri_close, monday_open))
        tuesday_open = next_session_open(monday_open + 60)
        self.assertFalse(fill_is_next_open(fri_close, tuesday_open))


class FillExpiryTests(unittest.TestCase):
    def _book(self, decided):
        b = PaperBook(started="x")
        b.positions = [Position("AAPL", 0.1, decided, 100.0)]
        return b

    def test_next_open_fills_and_measures_slippage(self):
        decided = ts(2026, 11, 13, 16, 0)
        candles = {"AAPL": [Candle(ts=int(decided), open=100, high=101, low=99, close=100, volume=1),
                            Candle(ts=int(decided + 65.5 * 3600), open=100.5, high=101,
                                   low=100, close=100.4, volume=1)]}
        book = self._book(decided)
        filled = apply_fills(book, candles)
        self.assertEqual(len(filled), 1)
        self.assertAlmostEqual(book.slippage_bps[0], 50.0, places=2)

    def test_a_much_later_bar_expires_instead_of_filling(self):
        decided = ts(2026, 11, 13, 16, 0)
        candles = {"AAPL": [Candle(ts=int(decided + 20 * 86400), open=140, high=141,
                                   low=139, close=140, volume=1)]}
        book = self._book(decided)
        filled = apply_fills(book, candles)
        self.assertEqual(filled, [])
        self.assertEqual(book.slippage_bps, [])      # drift is never booked as cost
        self.assertEqual(len(book.expired), 1)
        self.assertIn("stale", book.expired[0]["reason"])
        self.assertEqual(book.positions, [])

    def test_closed_market_leaves_the_decision_pending(self):
        decided = ts(2026, 11, 14, 10, 0)           # a Saturday
        book = self._book(decided)
        self.assertEqual(apply_fills(book, {"AAPL": []}), [])
        self.assertEqual(len(book.positions), 1)
        self.assertEqual(book.sessions, 0)          # a run that did nothing is not a session

    def test_expiry_survives_a_round_trip_to_json(self):
        decided = ts(2026, 11, 13, 16, 0)
        book = self._book(decided)
        apply_fills(book, {"AAPL": [Candle(ts=int(decided + 30 * 86400), open=1, high=1,
                                           low=1, close=1, volume=1)]})
        again = PaperBook.from_json(book.to_json())
        self.assertEqual(len(again.expired), 1)


if __name__ == "__main__":
    unittest.main()
