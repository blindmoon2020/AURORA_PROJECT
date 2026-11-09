import json
import tempfile
import unittest
from pathlib import Path

from aurora.strategies import DnaError, EmaCross, load_dna, parse_dna

BASE = {
    "name": "t",
    "symbol": "EURUSD",
    "type": "ema_cross",
    "params": {"fast": 5, "slow": 20},
    "risk": {"risk_per_trade_pct": 0.5},
}


class DnaTests(unittest.TestCase):
    def test_parse_builds_strategy(self):
        dna = parse_dna(json.loads(json.dumps(BASE)))
        strat = dna.build()
        self.assertIsInstance(strat, EmaCross)
        self.assertEqual(dna.symbol, "EURUSD")
        self.assertAlmostEqual(dna.risk.risk_per_trade_pct, 0.5)

    def test_missing_keys_are_named(self):
        raw = dict(BASE)
        del raw["risk"]
        with self.assertRaises(DnaError) as ctx:
            parse_dna(raw)
        self.assertIn("risk", str(ctx.exception))

    def test_unknown_type_rejected(self):
        raw = dict(BASE, type="magic")
        with self.assertRaises(DnaError) as ctx:
            parse_dna(raw)
        self.assertIn("unknown strategy type", str(ctx.exception))

    def test_unknown_risk_key_rejected(self):
        raw = dict(BASE, risk={"risk_per_trade_pct": 0.5, "moon": 1})
        with self.assertRaises(DnaError) as ctx:
            parse_dna(raw)
        self.assertIn("unknown risk keys", str(ctx.exception))

    def test_invalid_params_rejected_at_load_time(self):
        raw = dict(BASE, params={"fast": 50, "slow": 20})
        with self.assertRaises(DnaError) as ctx:
            parse_dna(raw)
        self.assertIn("invalid params", str(ctx.exception))

    def test_load_shipped_dna(self):
        path = Path(__file__).resolve().parents[1] / "strategies" / "ema_cross_eurusd.json"
        dna = load_dna(path)
        self.assertEqual(dna.type, "ema_cross")
        self.assertTrue(dna.notes)

    def test_bad_file_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "broken.json"
            p.write_text("{not json", encoding="utf-8")
            with self.assertRaises(DnaError) as ctx:
                load_dna(p)
            self.assertIn("invalid JSON", str(ctx.exception))
            with self.assertRaises(DnaError):
                load_dna(Path(tmp) / "missing.json")


if __name__ == "__main__":
    unittest.main()
