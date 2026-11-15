import unittest

from aurora.saas import psychometric_engine as pe


def full_answers(option_index: int):
    return {q["id"]: option_index for q in pe.PSYCHOMETRIC_QUESTIONS}


class PsychometricTests(unittest.TestCase):
    def test_the_module_imports_and_scores(self):
        result = pe.assess(full_answers(3))
        self.assertIn(result["band"], ("محافظه‌کار", "متعادل", "رشدگرا", "تهاجمی", "محافظه‌کار متعادل"))
        self.assertGreaterEqual(result["score"], 0.0)

    def test_questionnaire_is_json_ready(self):
        items = pe.questionnaire_for_api()
        self.assertGreaterEqual(len(items), 6)
        self.assertTrue(all(q["options"] and "kind" in q for q in items))

    def test_max_appetite_scores_higher_than_minimum(self):
        low = pe.assess(full_answers(0))["score"]
        high = pe.assess(full_answers(3))["score"]
        self.assertGreater(high, low)

    def test_contradiction_is_reported_not_smoothed(self):
        result = pe.assess(full_answers(3), {"loss_tolerance_pct": 60, "horizon_years": 1,
                                            "emergency_fund_months": 0})
        self.assertTrue(result["contradictions"])

    def test_missing_answers_is_an_error_not_a_default(self):
        with self.assertRaises(ValueError):
            pe.assess({})


if __name__ == "__main__":
    unittest.main()
