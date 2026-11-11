from lidoma_engines.decision.quality import (
    DecisionQualityRanker,
)


def test_quality_ranking():

    result = DecisionQualityRanker().calculate(
        decision_id="decision.alpha",
        accuracy_score=1.0,
        confidence_score=0.8,
        reliability_score=0.9,
        outcome_score=1.0,
    )

    assert result.final_score == 0.93
    assert result.reason == (
        "decision_quality_ranking"
    )


def test_quality_average():

    result = DecisionQualityRanker().calculate(
        decision_id="decision.beta",
        accuracy_score=0.5,
        confidence_score=0.5,
        reliability_score=0.5,
        outcome_score=0.5,
    )

    assert result.final_score == 0.5


def test_invalid_decision_id():

    try:
        DecisionQualityRanker().calculate(
            decision_id="",
            accuracy_score=0.5,
            confidence_score=0.5,
            reliability_score=0.5,
            outcome_score=0.5,
        )

        assert False

    except ValueError:
        assert True