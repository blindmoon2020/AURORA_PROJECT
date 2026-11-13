import unittest

from aurora.net import throttle as th


class ThrottleTests(unittest.TestCase):
    def setUp(self):
        self.sleeps = []
        th._sleep = lambda s: self.sleeps.append(s)
        th._last_call[0] = float("-inf")
        th._clock = lambda: 0.0

    def tearDown(self):
        th._sleep = __import__("time").sleep
        th._clock = __import__("time").monotonic
        th._last_call[0] = float("-inf")

    def test_first_call_does_not_wait(self):
        self.assertEqual(th.throttle(7.6), 0.0)
        self.assertEqual(self.sleeps, [])

    def test_second_call_waits_the_gap(self):
        th._clock = lambda: 0.0
        th.throttle(7.6)
        th._clock = lambda: 2.0          # only two seconds have passed
        wait = th.throttle(7.6)
        self.assertAlmostEqual(wait, 5.6, places=3)
        self.assertEqual(len(self.sleeps), 1)

    def test_backoff_doubles_and_obeys_retry_after(self):
        self.assertEqual(th.retry_delay(0), 8.0)
        self.assertEqual(th.retry_delay(2), 32.0)
        self.assertEqual(th.retry_delay(0, retry_after=3.0), 3.0)


if __name__ == "__main__":
    unittest.main()
