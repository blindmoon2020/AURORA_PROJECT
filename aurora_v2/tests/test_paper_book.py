import unittest

from aurora.core.types import Candle
from aurora.execution.paper_book import (PaperBook, Position, apply_fills,
                                         mark_to_market, rebalance)


def bar(ts, o, c=None):
    c = o if c is None else c
    return Candle(ts=ts, open=o, high=max(o, c), low=min(o, c), close=c)


class FillTests(unittest.TestCase):
    def test_pending_fill_waits_for_the_next_open(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("AAPL", 0.1, decided_ts=100, decided_price=200.0)]
        self.assertEqual(apply_fills(book, {"AAPL": [bar(100, 200.0)]}), [])
        self.assertIsNone(book.positions[0].fill_price)

    def test_fill_is_next_open_and_slippage_is_signed(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("AAPL", 0.1, decided_ts=100, decided_price=200.0)]
        filled = apply_fills(book, {"AAPL": [bar(100, 200.0), bar(200, 202.0)]})
        self.assertAlmostEqual(book.positions[0].fill_price, 202.0)
        self.assertAlmostEqual(filled[0]["bps"], 100.0, places=6)

    def test_cheaper_fill_is_positive_slippage(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("X", 0.1, decided_ts=1, decided_price=100.0)]
        apply_fills(book, {"X": [bar(1, 100.0), bar(2, 99.0)]})
        self.assertAlmostEqual(book.slippage_bps[0], -100.0, places=6)

    def test_fills_are_not_applied_twice(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("X", 0.1, decided_ts=1, decided_price=100.0)]
        candles = {"X": [bar(1, 100.0), bar(2, 101.0), bar(3, 105.0)]}
        apply_fills(book, candles)
        apply_fills(book, candles)
        self.assertEqual(len(book.slippage_bps), 1)
        self.assertAlmostEqual(book.positions[0].fill_price, 101.0)


class BookTests(unittest.TestCase):
    def test_rebalance_reports_changes(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("OLD", 0.1, 1, 10.0)]
        changed = rebalance(book, {"NEW": 0.2}, {"NEW": (5, 50.0)})
        self.assertIn("exit OLD", changed)
        self.assertIn("enter NEW", changed)
        self.assertEqual([p.symbol for p in book.positions], ["NEW"])

    def test_mark_to_market_uses_fill_when_available(self):
        book = PaperBook(started="2026-11-13")
        book.positions = [Position("X", 0.5, 1, 100.0, fill_price=101.0, fill_ts=2)]
        eq = mark_to_market(book, {"X": (3, 111.1)})
        self.assertAlmostEqual(eq, 1.05, places=6)

    def test_roundtrip_json(self):
        book = PaperBook(started="2026-11-13", sessions=3)
        book.positions = [Position("X", 0.1, 1, 10.0)]
        blob = book.to_json()
        again = PaperBook.from_json(blob)
        self.assertEqual(again.sessions, 3)
        self.assertEqual(again.positions[0].symbol, "X")


if __name__ == "__main__":
    unittest.main()
