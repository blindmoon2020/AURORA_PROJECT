import unittest

from aurora.journal.attribution import (DECREASE, ENTER, EXIT, FLIP, HOLD, INCREASE,
                                        classify, describe, effective_cost_units,
                                        events, summarise)


class ClassifyTests(unittest.TestCase):
    def test_flip_is_detected_by_sign_not_by_size(self):
        self.assertEqual(classify(0.10, -0.05), FLIP)
        self.assertEqual(classify(-0.02, 0.02), FLIP)

    def test_resize_is_not_a_flip(self):
        self.assertEqual(classify(0.10, 0.15), INCREASE)
        self.assertEqual(classify(0.10, 0.05), DECREASE)

    def test_enter_and_exit(self):
        self.assertEqual(classify(0.0, 0.10), ENTER)
        self.assertEqual(classify(0.10, 0.0), EXIT)

    def test_no_position_either_side_is_hold(self):
        self.assertEqual(classify(0.0, 0.0), HOLD)


class EventTests(unittest.TestCase):
    def test_only_real_changes_are_listed(self):
        evs = events({"A": 0.10, "B": 0.10}, {"A": 0.10, "C": 0.10})
        kinds = {e.symbol: e.kind for e in evs}
        self.assertNotIn("A", kinds)
        self.assertEqual(kinds["B"], EXIT)
        self.assertEqual(kinds["C"], ENTER)

    def test_a_flip_costs_two_units(self):
        evs = events({"A": 0.10}, {"A": -0.10})
        self.assertEqual(evs[0].kind, FLIP)
        self.assertEqual(effective_cost_units(evs), 2)

    def test_resize_costs_one_unit(self):
        evs = events({"A": 0.10}, {"A": 0.20})
        self.assertEqual(effective_cost_units(evs), 1)

    def test_summary_and_description(self):
        evs = events({"A": 0.1, "B": 0.2}, {"A": -0.1, "B": 0.25, "C": 0.05})
        counts = summarise(evs)
        self.assertEqual((counts[FLIP], counts[INCREASE], counts[ENTER]), (1, 1, 1))
        text = describe(evs)
        self.assertIn("flip", text)
        self.assertIn("cost units", text)

    def test_empty_change_set_says_so(self):
        self.assertEqual(describe(events({"A": 0.1}, {"A": 0.1})), "no change")


if __name__ == "__main__":
    unittest.main()
