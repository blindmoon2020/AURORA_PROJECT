import importlib
import json
import tempfile
import unittest
from pathlib import Path

from aurora import core_contract as cc


class ContractTests(unittest.TestCase):
    def test_the_committed_contract_matches_the_core(self):
        ok, message = cc.check()
        self.assertTrue(ok, message)

    def test_the_contract_protects_a_meaningful_surface(self):
        contract = cc.load()
        self.assertGreaterEqual(len(contract), 10)
        self.assertGreaterEqual(sum(len(v) for v in contract.values()), 60)

    def test_a_removed_function_is_reported_missing(self):
        contract = {"aurora.calibration": {"calibrate": "(x)"}}
        missing, changed = cc.verify({"aurora.calibration": {}}, contract)
        self.assertEqual(missing, ["aurora.calibration.calibrate"])
        self.assertEqual(changed, [])

    def test_a_removed_module_is_reported_not_ignored(self):
        missing, _ = cc.verify({}, {"aurora.privacy": {"redact": "(x)"}})
        self.assertTrue(any("whole module" in m for m in missing))

    def test_a_changed_signature_is_reported(self):
        current = {"aurora.calibration": {"calibrate": "(a, b)"}}
        contract = {"aurora.calibration": {"calibrate": "(a)"}}
        missing, changed = cc.verify(current, contract)
        self.assertEqual(missing, [])
        self.assertEqual(len(changed), 1)

    def test_adding_a_function_is_not_a_violation(self):
        current = {"aurora.calibration": {"calibrate": "(a)", "brand_new": "(b)"}}
        contract = {"aurora.calibration": {"calibrate": "(a)"}}
        self.assertEqual(cc.verify(current, contract), ([], []))

    def test_the_trend_brake_that_was_once_destroyed_is_protected(self):
        # this is the exact function a careless overwrite removed; the contract exists
        # so that repeating that mistake fails loudly instead of braking silently
        self.assertIn("trend_brake", cc.load()["aurora.portfolio.overlay"])

    def test_reconcile_gate_is_protected(self):
        self.assertIn("require_clean", cc.load()["aurora.execution.reconcile"])

    def test_a_missing_contract_file_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, message = cc.check(Path(tmp) / "absent.json")
        self.assertFalse(ok)
        self.assertIn("missing", message)

    def test_writing_then_checking_a_temp_contract_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            cc.write(path)
            ok, _ = cc.check(path)
            self.assertTrue(ok)
            self.assertTrue(json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
