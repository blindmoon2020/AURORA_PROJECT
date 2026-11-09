import json
import tempfile
import unittest
from pathlib import Path

from aurora.journal import DecisionLog, DecisionRecord, read_log


def rec(**kw):
    base = dict(ts=1, symbol="EURUSD", strategy="ema_cross", side="long", entry=1.1,
                stop=1.095, target=1.11, units=2000.0, risk_money=10.0,
                equity=10000.0, approved=True, reason="test reason")
    base.update(kw)
    return DecisionRecord(**base)


class JournalTests(unittest.TestCase):
    def test_reason_is_mandatory(self):
        with self.assertRaises(ValueError):
            DecisionLog().record(rec(reason="  "))

    def test_in_memory_filters(self):
        log = DecisionLog()
        log.record(rec(approved=True))
        log.record(rec(approved=False, units=0.0, reason="daily loss cap hit"))
        self.assertEqual(len(log.approved()), 1)
        self.assertEqual(len(log.rejected()), 1)
        self.assertEqual(len(log), 2)

    def test_jsonl_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "decisions.jsonl"
            log = DecisionLog(path)
            log.record(rec(ts=10, approved=True))
            log.record(rec(ts=20, approved=False, units=0.0, reason="rejected for a reason"))
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(set(json.loads(lines[0])), set(DecisionRecord.__dataclass_fields__))
            back = read_log(path)
            self.assertEqual(len(back), 2)
            self.assertEqual(back[1].ts, 20)
            self.assertFalse(back[1].approved)
            self.assertTrue(back[1].reason)


if __name__ == "__main__":
    unittest.main()
