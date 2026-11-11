import tempfile
import unittest
from pathlib import Path

from aurora.instruments import (ASSET_CLASSES, by_class, get, load_listing, universe)


class InstrumentMasterTests(unittest.TestCase):
    def test_every_asset_class_is_populated(self):
        counts = by_class()
        for cls in ASSET_CLASSES:
            self.assertGreater(counts.get(cls, 0), 0, f"{cls} has no instrument")

    def test_symbols_are_unique(self):
        symbols = [i.symbol for i in universe()]
        self.assertEqual(len(symbols), len(set(symbols)))

    def test_canonical_lookup_and_yahoo_mapping(self):
        self.assertEqual(get("EURUSD").yahoo, "EURUSD=X")
        self.assertEqual(get("XAUUSD").yahoo, "XAUUSD=X")
        self.assertTrue(get("BTCUSD").has_volume)
        self.assertFalse(get("EURUSD").has_volume)
        with self.assertRaises(KeyError):
            get("NOPE")

    def test_filters(self):
        self.assertTrue(all(i.asset_class == "agri" for i in universe(asset_class="agri")))
        self.assertTrue(all(i.region == "us" for i in universe(region="us")))
        self.assertEqual(len(universe(asset_class="fx", region="em")), 18)

    def test_listing_loader(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "listing.csv"
            p.write_text("symbol,name,exchange,currency\nAAPL,Apple,NASDAQ,USD\n"
                         "7203,Toyota,TSE,JPY\n", encoding="utf-8")
            rows = load_listing(p, "equity")
        self.assertEqual([r.symbol for r in rows], ["AAPL", "7203"])
        self.assertEqual(rows[1].currency, "JPY")
        self.assertTrue(rows[0].has_volume)


if __name__ == "__main__":
    unittest.main()
