from lidoma_engines.decision.score_fusion import (
    AdaptiveDecisionScoreFusion,
)


def test_score_fusion():

    result = AdaptiveDecisionScoreFusion().calculate(
        consensus_score=0.9,
        calibrated_confidence=0.8,
        reliability_score=0.85,
        freshness_factor=1.0,
        governance_factor=1.0,
    )

    assert result.final_score == 0.89
    assert result.reason == (
        "adaptive_decision_score_fusion"
    )


def test_score_fusion_average():

    result = AdaptiveDecisionScoreFusion().calculate(
        consensus_score=0.5,
        calibrated_confidence=0.5,
        reliability_score=0.5,
        freshness_factor=0.5,
        governance_factor=0.5,
    )

    assert result.final_score == 0.5


def test_invalid_score():

    try:
        AdaptiveDecisionScoreFusion().calculate(
            consensus_score=1.5,
            calibrated_confidence=0.5,
            reliability_score=0.5,
            freshness_factor=0.5,
            governance_factor=0.5,
        )

        assert False

    except ValueError:
        assert True