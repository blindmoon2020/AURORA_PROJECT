import unittest

from aurora.advice import onboarding as ob


def answers(capacity_choice: int, tolerance_choice: int) -> dict:
    out = {}
    for q in ob.QUESTIONS:
        out[q["id"]] = capacity_choice if q["kind"] == "capacity" else tolerance_choice
    return out


class ContradictionTests(unittest.TestCase):
    def test_a_consistent_aggressive_client_raises_no_flag(self):
        flags = ob.contradictions(answers(3, 3), {"horizon_years": 15,
                                                  "emergency_fund_months": 12,
                                                  "loss_tolerance_pct": 10})
        self.assertEqual(flags, [])

    def test_appetite_above_capacity_is_a_flag(self):
        flags = ob.contradictions(answers(0, 3), {"horizon_years": 15,
                                                  "emergency_fund_months": 12,
                                                  "loss_tolerance_pct": 5})
        self.assertTrue(any("ظرفیت" in f for f in flags))

    def test_short_horizon_with_aggression_is_a_flag(self):
        flags = ob.contradictions(answers(3, 3), {"horizon_years": 1,
                                                  "emergency_fund_months": 12,
                                                  "loss_tolerance_pct": 5})
        self.assertTrue(any("افق" in f for f in flags))

    def test_no_buffer_with_aggression_is_a_flag(self):
        flags = ob.contradictions(answers(3, 3), {"horizon_years": 15,
                                                  "emergency_fund_months": 0,
                                                  "loss_tolerance_pct": 5})
        self.assertTrue(any("ذخیره" in f for f in flags))

    def test_a_loss_claim_above_the_profile_cap_is_a_flag(self):
        flags = ob.contradictions(answers(3, 3), {"horizon_years": 15,
                                                  "emergency_fund_months": 12,
                                                  "loss_tolerance_pct": 90})
        self.assertTrue(any("افت" in f for f in flags))

    def test_a_conservative_client_with_short_horizon_is_not_flagged(self):
        flags = ob.contradictions(answers(0, 0), {"horizon_years": 1,
                                                  "emergency_fund_months": 0,
                                                  "loss_tolerance_pct": 2})
        self.assertEqual(flags, [])


if __name__ == "__main__":
    unittest.main()
