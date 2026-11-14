import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from aurora import privacy
from aurora.vault import (CustomerVault, VaultError, aggregate_holdings, classify,
                          protect)

KEY = "unit-test-pseudonym-key"


class VaultTests(unittest.TestCase):
    def setUp(self):
        os.environ["AURORA_PSEUDONYM_KEY"] = KEY

    def tearDown(self):
        os.environ.pop("AURORA_PSEUDONYM_KEY", None)

    def test_bank_account_never_written_in_the_clear(self):
        safe = protect({"customer_id": "c-17", "iban": "IR820540102680020817909002",
                        "cash_balance": 125000})
        self.assertNotIn("IR820540102680020817909002", json.dumps(safe))
        self.assertTrue(safe["iban__redacted"])
        self.assertEqual(safe["cash_balance"], 125000)

    def test_no_key_means_refusal_not_a_leak(self):
        os.environ.pop("AURORA_PSEUDONYM_KEY", None)
        with self.assertRaises(VaultError):
            protect({"iban": "IR820540102680020817909002"})

    def test_unknown_field_is_confidential_by_default(self):
        self.assertEqual(classify("mystery_column"), "confidential")
        safe = protect({"mystery_column": "x"})
        self.assertEqual(safe["mystery_column"], "x")

    def test_trades_keep_what_analysis_needs_and_lose_who(self):
        safe = protect({"customer_id": "c-17", "symbol": "AAPL", "side": "BUY",
                        "quantity": 10, "price": 355.63})
        self.assertEqual(safe["symbol"], "AAPL")
        self.assertEqual(safe["price"], 355.63)
        self.assertNotEqual(safe["customer_id"], "c-17")

    def test_vault_file_is_private_and_logged(self):
        with tempfile.TemporaryDirectory() as d:
            v = CustomerVault(Path(d) / "customers.jsonl")
            v.write("open_account", {"customer_id": "c-1", "email": "a@b.com"})
            mode = stat.S_IMODE(os.stat(v.path).st_mode)
            self.assertEqual(mode, 0o600)
            self.assertIsNone(v.log.verify_chain())
            self.assertEqual(v.log.entries[0]["event"], "open_account")
            self.assertNotIn("a@b.com", v.path.read_text())

    def test_reads_are_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            v = CustomerVault(Path(d) / "c.jsonl")
            v.write("open", {"customer_id": "c-1"})
            v.read_rows()
            self.assertEqual([e["event"] for e in v.log.entries], ["open", "read"])

    def test_tampering_breaks_the_chain(self):
        with tempfile.TemporaryDirectory() as d:
            v = CustomerVault(Path(d) / "c.jsonl")
            v.write("open", {"customer_id": "c-1"})
            v.write("trade", {"customer_id": "c-1", "symbol": "XOM"})
            v.log.entries[0]["payload"] = "edited"
            self.assertEqual(v.log.verify_chain(), 0)

    def test_aggregate_has_no_customer(self):
        agg = aggregate_holdings([{"symbol": "AAPL", "quantity": 5},
                                  {"symbol": "AAPL", "quantity": 7},
                                  {"symbol": "XOM", "quantity": 2}])
        self.assertEqual(agg, {"AAPL": 12.0, "XOM": 2.0})

    def test_public_view_drops_personal_and_confidential(self):
        with tempfile.TemporaryDirectory() as d:
            v = CustomerVault(Path(d) / "c.jsonl")
            v.write("open", {"customer_id": "c-1", "symbol": "AAPL", "quantity": 3,
                             "price": 100})
            row = v.public_view()[0]
            self.assertIn("symbol", row)
            self.assertNotIn("quantity", row)
            self.assertNotIn("customer_id", row)


if __name__ == "__main__":
    unittest.main()
