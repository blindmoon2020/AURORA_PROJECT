import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from aurora.core import asset_universe as au
from scripts.export_catalogue import export


class ExportTests(unittest.TestCase):
    def build(self):
        tmp = TemporaryDirectory()
        payload = export(Path(tmp.name))
        return tmp, payload

    def test_every_instrument_is_exported(self):
        tmp, payload = self.build()
        self.assertEqual(len(payload["instruments"]), len(au.INSTRUMENTS))
        tmp.cleanup()

    def test_counts_match_the_module(self):
        tmp, payload = self.build()
        self.assertEqual(payload["counts"]["instruments"], len(au.INSTRUMENTS))
        self.assertEqual(payload["counts"]["verified"] + payload["counts"]["assumed"],
                         len(au.INSTRUMENTS))
        tmp.cleanup()

    def test_both_files_are_written(self):
        tmp, payload = self.build()
        self.assertTrue((Path(tmp.name) / "docs/catalogue.json").exists())
        self.assertTrue((Path(tmp.name) / "docs/CATALOGUE_OFFICIAL.md").exists())
        tmp.cleanup()

    def test_the_json_is_valid_and_round_trips(self):
        tmp, _ = self.build()
        raw = (Path(tmp.name) / "docs/catalogue.json").read_text(encoding="utf-8")
        self.assertEqual(json.loads(raw)["document"], "AURORA instrument catalogue")
        tmp.cleanup()

    def test_the_official_document_states_that_an_assumption_is_not_verified(self):
        tmp, _ = self.build()
        text = (Path(tmp.name) / "docs/CATALOGUE_OFFICIAL.md").read_text(encoding="utf-8")
        self.assertIn("فرض ≠ تأیید", text)
        self.assertIn("این سند دستی ویرایش نمی‌شود", text)
        tmp.cleanup()

    def test_the_document_names_all_the_classes_the_owner_asked_for(self):
        tmp, _ = self.build()
        text = (Path(tmp.name) / "docs/CATALOGUE_OFFICIAL.md").read_text(encoding="utf-8")
        for label in ("جفت‌ارز", "فلزات", "کالای کشاورزی", "ETF", "صندوق", "اوراق"):
            self.assertIn(label, text)
        tmp.cleanup()

    def test_an_unaudited_catalogue_cannot_export_clean(self):
        tmp, payload = self.build()
        self.assertEqual(payload["structural_audit"], [])
        tmp.cleanup()

    def test_the_export_is_deterministic_apart_from_the_timestamp(self):
        a = TemporaryDirectory(); b = TemporaryDirectory()
        pa = export(Path(a.name)); pb = export(Path(b.name))
        self.assertEqual(pa["instruments"], pb["instruments"])
        a.cleanup(); b.cleanup()


if __name__ == "__main__":
    unittest.main()
