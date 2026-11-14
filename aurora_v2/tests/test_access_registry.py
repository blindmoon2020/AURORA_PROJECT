import unittest

from aurora.core import access_registry as ar


class RegistryTests(unittest.TestCase):
    def test_the_registry_is_structurally_sound(self):
        self.assertEqual(ar.audit(), [])

    def test_every_path_is_https(self):
        for path in ar.PATHS:
            self.assertTrue(path.url.startswith("https://"), path.key)

    def test_the_owner_asked_for_links_so_every_blocker_has_one(self):
        from aurora.core import asset_universe  # noqa: F401  (registry must stand alone)
        keys = {p.key for p in ar.PATHS}
        for required in ("mofid", "tsetmc", "codal", "fred", "eodhd", "forexfactory",
                         "binance", "licence"):
            self.assertIn(required, keys)

    def test_free_paths_are_identified(self):
        self.assertGreaterEqual(len(ar.free_paths()), 8)

    def test_unverified_links_are_named_not_hidden(self):
        self.assertIn("mofid", ar.unverified())

    def test_an_unknown_key_raises(self):
        with self.assertRaises(ar.UnknownAccessPath):
            ar.by_key("nope")

    def test_the_markdown_states_the_security_rule(self):
        text = ar.markdown()
        self.assertIn("فرم امن", text)
        self.assertIn("برداشت", text)

    def test_every_kind_appears_in_the_markdown(self):
        text = ar.markdown()
        for path in ar.PATHS:
            self.assertIn(path.url, text)

    def test_counts_add_up(self):
        self.assertEqual(sum(ar.counts().values()), len(ar.PATHS))


if __name__ == "__main__":
    unittest.main()
