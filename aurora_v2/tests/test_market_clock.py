import unittest
from datetime import datetime, timezone

from aurora.core import market_clock as mc


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class ClockTests(unittest.TestCase):
    def test_new_york_is_open_in_the_afternoon_utc(self):
        # Wednesday 15:00 UTC is 10:00 EST: mid-session
        ok, why = mc.is_venue_open("XNYS", utc(2026, 11, 18, 15, 0))
        self.assertTrue(ok, why)

    def test_new_york_is_shut_at_the_weekend(self):
        ok, why = mc.is_venue_open("XNYS", utc(2026, 11, 15, 15, 0))   # Sunday
        self.assertFalse(ok)
        self.assertIn("تعطیل", why)

    def test_new_york_is_shut_after_the_close(self):
        ok, why = mc.is_venue_open("XNYS", utc(2026, 11, 18, 22, 0))   # 17:00 EST
        self.assertFalse(ok)
        self.assertIn("خارج از ساعت", why)

    def test_tehran_trades_on_saturday(self):
        ok, why = mc.is_venue_open("XTSE_IR", utc(2026, 11, 14, 6, 0))  # Sat 09:30 Tehran
        self.assertTrue(ok, why)

    def test_tehran_is_shut_on_friday(self):
        ok, _ = mc.is_venue_open("XTSE_IR", utc(2026, 11, 13, 6, 0))
        self.assertFalse(ok)

    def test_crypto_never_closes(self):
        ok, why = mc.is_venue_open("XCRYPTO", utc(2026, 11, 15, 3, 0))
        self.assertTrue(ok, why)

    def test_unknown_venue_is_closed_not_assumed_open(self):
        ok, why = mc.is_venue_open("XNOPE", utc(2026, 11, 18, 15, 0))
        self.assertFalse(ok)
        self.assertIn("نامعلوم", why)

    def test_instrument_gate_names_the_venue(self):
        ok, why = mc.gate("AAPL", utc(2026, 11, 18, 15, 0))
        self.assertTrue(ok)
        self.assertIn("نزدک", why)

    def test_unknown_symbol_is_refused_with_a_reason(self):
        ok, why = mc.gate("NOPE-XX", utc(2026, 11, 18, 15, 0))
        self.assertFalse(ok)
        self.assertIn("نامعلوم", why)


if __name__ == "__main__":
    unittest.main()
