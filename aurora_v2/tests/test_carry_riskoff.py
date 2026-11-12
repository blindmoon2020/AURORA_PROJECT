import unittest

from aurora.strategies.carry_riskoff import (apply_defences, inverse_vol_scale,
                                             regime_mask)

DAY = 86_400
TS = [i * DAY for i in range(10)]


class RegimeTests(unittest.TestCase):
    def test_stress_switches_the_book_off(self):
        vix = {0: 12.0, 5 * DAY: 30.0}
        mask = regime_mask(TS, vix, vix_cut=25.0)
        # the reading published on day 5 is already 30, so the book is off that day
        self.assertEqual(mask[:5], [1.0] * 5)
        self.assertEqual(mask[5:], [0.0] * 5)

    def test_missing_vix_means_off_not_on(self):
        mask = regime_mask(TS, {5 * DAY: 12.0}, vix_cut=25.0)
        self.assertEqual(mask[:5], [0.0] * 5)
        self.assertEqual(mask[5:], [1.0] * 5)

    def test_credit_spread_can_shut_it_too(self):
        vix = {0: 12.0}
        spread = {0: 3.0, 4 * DAY: 7.5}
        mask = regime_mask(TS, vix, spread, vix_cut=25.0, spread_cut=5.0)
        self.assertEqual(mask[:4], [1.0] * 4)
        self.assertEqual(mask[4:], [0.0] * 6)


class ScaleTests(unittest.TestCase):
    def test_higher_vol_gets_a_smaller_position(self):
        calm = [0.001, -0.001] * 40
        wild = [0.02, -0.02] * 40
        s_calm = inverse_vol_scale(calm, target=0.10, cap=3.0)[-1]
        s_wild = inverse_vol_scale(wild, target=0.10, cap=3.0)[-1]
        self.assertGreater(s_calm, s_wild)
        self.assertLessEqual(s_calm, 3.0)

    def test_zero_vol_returns_zero_not_infinity(self):
        self.assertEqual(inverse_vol_scale([0.0] * 100)[-1], 0.0)


class ApplyTests(unittest.TestCase):
    def test_defences_multiply_and_validate_length(self):
        pos = [1.0] * 5
        self.assertEqual(apply_defences(pos, scale=[2.0] * 5, mask=[1, 1, 0, 0, 1]),
                         [2.0, 2.0, 0.0, 0.0, 2.0])
        with self.assertRaises(ValueError):
            apply_defences(pos, scale=[1.0])
