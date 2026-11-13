import unittest

from aurora.portfolio.overlay import trend_brake, vol_target


class VolTargetTests(unittest.TestCase):
    def test_no_history_means_no_position(self):
        self.assertEqual(vol_target([0.05, 0.04], window=6), [0.0, 0.0])

    def test_high_volatility_shrinks_the_return(self):
        # compare the scaling applied, not the raw size: a wild return stays
        # numerically larger even after being cut harder
        calm = [0.01, -0.01] * 10
        wild = [0.10, -0.10] * 10
        calm_scale = vol_target(calm, target=0.12, window=6)[-1] / calm[-1]
        wild_scale = vol_target(wild, target=0.12, window=6)[-1] / wild[-1]
        self.assertLess(wild_scale, calm_scale)

    def test_cap_prevents_leverage(self):
        tiny = [0.0001, -0.0001] * 10
        out = vol_target(tiny, target=0.12, window=6, cap=1.0)
        self.assertTrue(all(abs(o) <= 0.0001 + 1e-12 for o in out[2:]))

    def test_future_does_not_change_the_past(self):
        base = [0.02, -0.01, 0.03, 0.01, -0.02, 0.04, 0.01, -0.03]
        longer = base + [0.9, -0.9]
        self.assertEqual(vol_target(base, window=4)[:4], vol_target(longer, window=4)[:4])


class TrendBrakeTests(unittest.TestCase):
    def test_book_off_when_benchmark_below_its_past(self):
        bench = [0.05] * 10 + [-0.20] * 5
        rets = [0.01] * 15
        out = trend_brake(rets, bench, window=3)
        self.assertEqual(out[-1], 0.0)
        self.assertEqual(out[0], 0.01)

    def test_book_on_when_trend_up(self):
        bench = [0.02] * 12
        out = trend_brake([0.01] * 12, bench, window=3)
        self.assertTrue(all(o == 0.01 for o in out))

    def test_lengths_must_match(self):
        with self.assertRaises(ValueError):
            trend_brake([0.01], [0.01, 0.02], window=2)


if __name__ == "__main__":
    unittest.main()
