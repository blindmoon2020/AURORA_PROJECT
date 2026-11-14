import os
import unittest

from aurora.privacy import AuditLog, Field, luhn, pseudonym, redact, safe_export


class RedactTests(unittest.TestCase):
    def test_email_is_masked(self):
        self.assertEqual(redact("write to aziz@gmail.com now"), "write to *** now")

    def test_iranian_mobile_is_masked(self):
        self.assertNotIn("09121234567", redact("call 09121234567 today"))

    def test_card_number_is_masked_only_when_it_checks_out(self):
        self.assertEqual(redact("4111 1111 1111 1111"), "***")
        self.assertEqual(redact("1234567890123456"), "1234567890123456")

    def test_luhn_rejects_a_price_like_number(self):
        self.assertFalse(luhn("7620.50"))
        self.assertTrue(luhn("4111111111111111"))

    def test_prices_and_dates_survive(self):
        text = "AAPL closed at 355.63 on 2026-11-13"
        self.assertEqual(redact(text), text)


class PseudonymTests(unittest.TestCase):
    def setUp(self):
        os.environ["AURORA_PSEUDONYM_KEY"] = "test-key-not-real"

    def test_stable_and_namespaced(self):
        a = pseudonym("aziz@example.com", "user")
        self.assertEqual(a, pseudonym("aziz@example.com", "user"))
        self.assertNotEqual(a, pseudonym("aziz@example.com", "broker"))
        self.assertNotIn("aziz", a)

    def test_missing_key_refuses_rather_than_guessing(self):
        os.environ.pop("AURORA_PSEUDONYM_KEY", None)
        with self.assertRaises(RuntimeError):
            pseudonym("x")


class ExportTests(unittest.TestCase):
    def test_personal_fields_are_dropped_for_an_outside_audience(self):
        rows = [{"symbol": "AAPL", "email": "a@b.com", "note": "internal"}]
        schema = [Field("symbol", "public"), Field("email", "personal"),
                  Field("note", "internal")]
        self.assertEqual(safe_export(rows, schema), [{"symbol": "AAPL", "note": "internal"}])
        self.assertEqual(safe_export(rows, schema, allow=("public",)),
                         [{"symbol": "AAPL"}])

    def test_unknown_classification_is_a_named_error(self):
        with self.assertRaises(ValueError):
            Field("x", "secret-ish")


class AuditTests(unittest.TestCase):
    def test_chain_verifies_when_untouched(self):
        log = AuditLog()
        log.append("decision", "bought AAPL")
        log.append("access", "read prices for aziz@example.com")
        self.assertIsNone(log.verify_chain())

    def test_editing_history_is_detected_at_the_edited_entry(self):
        log = AuditLog()
        log.append("decision", "bought AAPL")
        log.append("decision", "sold AAPL")
        log.entries[0]["payload"] = "bought TSLA"
        self.assertEqual(log.verify_chain(), 0)

    def test_personal_data_never_lands_in_the_log(self):
        log = AuditLog()
        entry = log.append("contact", "email aziz@example.com")
        self.assertNotIn("aziz@example.com", entry["payload"])


if __name__ == "__main__":
    unittest.main()
