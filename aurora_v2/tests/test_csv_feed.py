import tempfile
import unittest
from pathlib import Path

from aurora.core.types import Candle
from aurora.data import CsvFeedError, load_csv, synthetic_candles, write_csv


class CsvFeedTests(unittest.TestCase):
    def test_roundtrip(self):
        candles = synthetic_candles(n=50, seed=3)
        with tempfile.TemporaryDirectory() as tmp:
            p = write_csv(candles, Path(tmp) / "x.csv")
            back = load_csv(p)
        self.assertEqual(len(back), 50)
        self.assertAlmostEqual(back[0].close, candles[0].close, places=9)
        self.assertEqual(back[-1].ts, candles[-1].ts)

    def test_header_aliases_and_iso_timestamps(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "iso.csv"
            p.write_text(
                "Date,Open,High,Low,Close\n"
                "2026-01-01T00:00:00Z,1.10,1.12,1.09,1.11\n"
                "2026-01-01T01:00:00Z,1.11,1.13,1.10,1.12\n",
                encoding="utf-8",
            )
            candles = load_csv(p)
        self.assertEqual(len(candles), 2)
        self.assertGreater(candles[0].ts, 0)
        self.assertLess(candles[0].ts, candles[1].ts)

    def test_missing_column_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.csv"
            p.write_text("ts,open,high,close\n1,1,1,1\n", encoding="utf-8")
            with self.assertRaises(CsvFeedError) as ctx:
                load_csv(p)
            self.assertIn("missing columns", str(ctx.exception))

    def test_bad_row_raises_with_line_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad2.csv"
            p.write_text("ts,open,high,low,close\n1,1.0,1.1,0.9,1.0\n2,1.0,oops,0.9,1.0\n",
                         encoding="utf-8")
            with self.assertRaises(CsvFeedError) as ctx:
                load_csv(p)
            self.assertIn("row 3", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
