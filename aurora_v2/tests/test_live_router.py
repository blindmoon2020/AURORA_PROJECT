import unittest

from aurora.core.asset_universe import UnknownInstrument
from aurora.execution import live_router as lr


class RoutingTests(unittest.TestCase):
    def test_iran_equities_go_through_a_manual_ticket(self):
        plan = lr.route_symbol("فولاد")
        self.assertEqual(plan.kind, lr.MANUAL)
        self.assertFalse(plan.blocked)
        self.assertIn("API معاملاتی ندارد", plan.reason)

    def test_iran_commodities_are_manual_too(self):
        self.assertEqual(lr.route_symbol("زعفران_نگین").kind, lr.MANUAL)

    def test_a_us_equity_without_broker_api_stays_on_the_simulator(self):
        self.assertEqual(lr.route_symbol("AAPL").kind, lr.PAPER)

    def test_a_us_equity_with_broker_api_uses_it(self):
        plan = lr.route_symbol("AAPL", has_broker_api=True)
        self.assertEqual(plan.kind, lr.API)
        self.assertFalse(plan.blocked)

    def test_crypto_without_keys_is_blocked_not_silently_paper(self):
        plan = lr.route_symbol("BTC-USD")
        self.assertTrue(plan.blocked)
        self.assertEqual(plan.kind, lr.BLOCKED)
        self.assertIn("کلید", plan.reason)

    def test_crypto_with_keys_routes_to_the_api(self):
        plan = lr.route_symbol("BTC-USD", has_exchange_keys=True)
        self.assertEqual(plan.kind, lr.API)
        self.assertFalse(plan.blocked)

    def test_otc_fx_is_blocked_because_no_usable_broker_is_guaranteed(self):
        plan = lr.route_symbol("EURUSD")
        self.assertTrue(plan.blocked)
        self.assertIn("مقیم ایران", plan.reason)

    def test_an_unknown_symbol_raises(self):
        with self.assertRaises(UnknownInstrument):
            lr.route_symbol("NOPE")

    def test_no_blocked_venue_ever_reports_a_success_route(self):
        for symbol in ("BTC-USD", "EURUSD", "SAND-USD"):
            plan = lr.route_symbol(symbol)
            if plan.blocked:
                self.assertEqual(plan.kind, lr.BLOCKED)


class BookTests(unittest.TestCase):
    def test_the_book_counts_each_route(self):
        book = lr.route_book({"AAPL": 0.1, "فولاد": 0.1, "BTC-USD": 0.05})
        counts = book.counts()
        self.assertEqual(counts.get(lr.PAPER), 1)
        self.assertEqual(counts.get(lr.MANUAL), 1)
        self.assertEqual(counts.get("blocked"), 1)

    def test_blocked_symbols_are_listed(self):
        book = lr.route_book({"AAPL": 0.1, "EURUSD": 0.1})
        self.assertEqual(lr.unroutable(book.plans), ["EURUSD"])

    def test_the_report_names_the_blocked_markets_and_the_reason(self):
        text = lr.route_report(lr.route_book({"EURUSD": 0.1, "فولاد": 0.1}))
        self.assertIn("EURUSD", text)
        self.assertIn("مسیر ندارند", text)
        self.assertIn("فولاد", text)

    def test_one_blocked_market_does_not_block_the_others(self):
        book = lr.route_book({"AAPL": 0.2, "EURUSD": 0.1})
        tradable = [p for p in book.plans if not p.blocked]
        self.assertEqual([p.symbol for p in tradable], ["AAPL"])

    def test_an_empty_book_is_empty_not_an_error(self):
        book = lr.route_book({})
        self.assertEqual(book.plans, [])
        self.assertIn("مسیرهای اجرا", book.summary())


if __name__ == "__main__":
    unittest.main()
