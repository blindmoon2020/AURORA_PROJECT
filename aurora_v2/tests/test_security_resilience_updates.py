import unittest

from aurora import resilience, updates
from aurora.security import MASK, assert_safe, contains_secret, redact


class SecurityTests(unittest.TestCase):
    def test_known_secret_is_masked(self):
        out = redact("key=SUPERSECRETVALUE123 ok", secrets=["SUPERSECRETVALUE123"])
        self.assertNotIn("SUPERSECRET", out)
        self.assertIn(MASK, out)

    def test_key_shaped_token_is_masked_even_when_unknown(self):
        token = "abcdefghijklmnopqrstuvwxyz0123456789"
        self.assertNotIn(token, redact(f"leaked {token}"))

    def test_ordinary_text_and_prices_survive(self):
        text = "AAPL 355.63 +1.2% on 2026-11-13"
        self.assertEqual(redact(text, secrets=[]), text)
        self.assertFalse(contains_secret(text, secrets=[]))

    def test_publishing_a_secret_is_refused_not_sanitised(self):
        with self.assertRaises(PermissionError):
            assert_safe("token=abcdefghijklmnopqrstuvwxyz0123456789", "commit")


class ResilienceTests(unittest.TestCase):
    def test_live_when_fresh(self):
        state = resilience.assess("1d", age_hours=2.0, fetch_failed=False)
        self.assertEqual(state.mode, resilience.LIVE)
        self.assertTrue(state.may_open_positions)

    def test_cached_allows_management_but_not_new_risk(self):
        state = resilience.assess("1d", age_hours=60.0, fetch_failed=True)
        self.assertEqual(state.mode, resilience.CACHED)
        self.assertTrue(state.usable)
        self.assertFalse(state.may_open_positions)

    def test_stale_hourly_cache_is_offline_not_degraded(self):
        state = resilience.assess("1h", age_hours=100.0, fetch_failed=True)
        self.assertEqual(state.mode, resilience.OFFLINE)
        self.assertFalse(state.usable)

    def test_no_cache_and_no_network_is_offline(self):
        state = resilience.assess("1d", age_hours=None, fetch_failed=True)
        self.assertEqual(state.mode, resilience.OFFLINE)
        self.assertIn("no cache", state.stamp())


class UpdateTests(unittest.TestCase):
    def test_first_sighting_is_not_a_change(self):
        d = updates.digest("src", ["date", "close"], [[1, 2]])
        self.assertEqual(updates.compare(None, d), [])

    def test_renamed_column_blocks_the_dataset(self):
        before = updates.digest("src", ["date", "close"], [[1, 2]])
        after = updates.digest("src", ["date", "adj_close"], [[1, 2]])
        changes = updates.compare(before, after)
        self.assertIn(updates.SCHEMA, [c.kind for c in changes])
        self.assertEqual(updates.blocked(changes), ["src"])

    def test_price_changes_do_not_alarm(self):
        before = updates.digest("src", ["date", "close"], [[1, 2]])
        after = updates.digest("src", ["date", "close"], [[2, 3]])
        self.assertEqual([c for c in updates.compare(before, after) if c.kind == updates.SCHEMA], [])

    def test_frozen_source_is_reported(self):
        rows = [[i, i * 2] for i in range(50)]
        before = updates.digest("src", ["a", "b"], rows)
        after = updates.digest("src", ["a", "b"], rows)
        self.assertIn(updates.CONTENT, [c.kind for c in updates.compare(before, after)])


if __name__ == "__main__":
    unittest.main()
