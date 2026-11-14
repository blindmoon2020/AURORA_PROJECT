import unittest

from aurora import resilience


class SessionStateTests(unittest.TestCase):
    def test_fresh_data_allows_new_risk(self):
        s = resilience.session_state(3.0, "1d")
        self.assertEqual(s.mode, resilience.LIVE)
        self.assertTrue(s.may_open_positions)

    def test_recent_but_stale_data_holds_and_forbids_new_risk(self):
        s = resilience.session_state(200.0, "1d")    # above the 120h limit, under 360h
        self.assertEqual(s.mode, resilience.CACHED)
        self.assertFalse(s.may_open_positions)

    def test_ancient_data_stops_the_session(self):
        s = resilience.session_state(5000.0, "1d")
        self.assertEqual(s.mode, resilience.OFFLINE)
        self.assertFalse(s.usable)

    def test_forced_offline_downgrades_even_fresh_data(self):
        self.assertEqual(resilience.session_state(1.0, "1d", forced_offline=True).mode,
                         resilience.CACHED)

    def test_hourly_limits_are_much_tighter_than_daily(self):
        self.assertEqual(resilience.session_state(40.0, "1h").mode, resilience.CACHED)
        self.assertEqual(resilience.session_state(40.0, "1d").mode, resilience.LIVE)

    def test_age_never_goes_negative(self):
        self.assertEqual(resilience.age_hours_of(100.0, 50.0), 0.0)


if __name__ == "__main__":
    unittest.main()
