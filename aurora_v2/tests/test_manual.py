import unittest

from aurora.core.types import Side
from aurora.execution.manual import (ManualExecutionError, parse_fills, reconcile,
                                     render, ticket)

HEADER = "ticket_id,ts,symbol,side,units,price,fee\n"


class TicketTests(unittest.TestCase):
    def test_expiry_is_set_and_units_must_be_positive(self):
        t = ticket("D1", "EURUSD", Side.LONG, 10, 1000, ttl_seconds=600)
        self.assertEqual(t.expires_ts, 1600)
        with self.assertRaises(ManualExecutionError):
            ticket("D1", "EURUSD", Side.LONG, 0, 1000)
        with self.assertRaises(ManualExecutionError):
            ticket("D1", "EURUSD", Side.LONG, 10, 1000, ttl_seconds=0)

    def test_render_shows_side_and_limit(self):
        text = render([ticket("D1", "XAUUSD", Side.SHORT, 2, 1000, limit_price=3950)])
        self.assertIn("SELL", text)
        self.assertIn("XAUUSD", text)
        self.assertIn("3950", text)


class FillParsingTests(unittest.TestCase):
    def test_persian_and_english_sides_are_both_accepted(self):
        text = HEADER + "D1-01,10,X,خرید,5,100,0\nD1-02,11,X,SELL,3,101,1\n"
        fills = parse_fills(text)
        self.assertEqual([f.side for f in fills], [Side.LONG, Side.SHORT])

    def test_missing_column_is_refused_not_guessed(self):
        with self.assertRaises(ManualExecutionError) as ctx:
            parse_fills("ticket_id,ts,symbol,side,units\nD1-01,10,X,BUY,5\n")
        self.assertIn("price", str(ctx.exception))

    def test_nonsense_rows_are_refused(self):
        for bad in ("D1-01,10,X,WHAT,5,100,0\n", "D1-01,10,X,BUY,-5,100,0\n",
                    "D1-01,10,X,BUY,5,0,0\n"):
            with self.assertRaises(ManualExecutionError):
                parse_fills(HEADER + bad)

    def test_byte_order_mark_does_not_break_the_header(self):
        self.assertEqual(len(parse_fills("\ufeff" + HEADER + "D1-01,10,X,BUY,5,100,0\n")), 1)


class ReconciliationTests(unittest.TestCase):
    def test_unfilled_ticket_is_named(self):
        t = ticket("D1", "EURUSD", Side.LONG, 1, 1000, limit_price=1.10)
        out = reconcile([t], [])
        self.assertEqual(len(out.unfilled), 1)
        self.assertEqual(out.matched, [])

    def test_unrecognised_fill_is_named(self):
        fills = parse_fills(HEADER + "GHOST-01,10,X,BUY,5,100,0\n")
        out = reconcile([], fills)
        self.assertEqual(len(out.unexpected), 1)

    def test_slippage_sign_follows_the_side(self):
        long_t = ticket("D1", "X", Side.LONG, 1, 1000, limit_price=100)
        short_t = ticket("D2", "X", Side.SHORT, 1, 1000, limit_price=100)
        fills = parse_fills(HEADER + "D1-01,10,X,BUY,1,101,0\nD2-01,10,X,SELL,1,101,0\n")
        out = reconcile([long_t, short_t], fills)
        self.assertGreater(out.price_slippage_bps[0], 0)    # paid above the limit
        self.assertLess(out.price_slippage_bps[1], 0)       # sold above the limit: good

    def test_a_ticket_cannot_be_filled_twice_or_in_the_wrong_direction(self):
        t = ticket("D1", "X", Side.LONG, 1, 1000, limit_price=100)
        twice = parse_fills(HEADER + "D1-01,10,X,BUY,1,100,0\nD1-01,11,X,BUY,1,100,0\n")
        with self.assertRaises(ManualExecutionError):
            reconcile([t], twice)
        wrong = parse_fills(HEADER + "D1-01,10,X,SELL,1,100,0\n")
        with self.assertRaises(ManualExecutionError):
            reconcile([t], wrong)


if __name__ == "__main__":
    unittest.main()
