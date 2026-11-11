from lidoma_engines.decision import (
    AdaptiveDecisionScoreFusion,
    DecisionQualityRanker,
    DecisionRuntimeIntegration,
)


def test_phase_6_end_to_end_pipeline():

    adaptive_score = AdaptiveDecisionScoreFusion().calculate(
        consensus_score=0.9,
        calibrated_confidence=0.85,
        reliability_score=0.9,
        freshness_factor=1.0,
        governance_factor=1.0,
    )

    quality_score = DecisionQualityRanker().calculate(
        decision_id="phase6.final.decision",
        accuracy_score=0.9,
        confidence_score=0.85,
        reliability_score=0.9,
        outcome_score=1.0,
    )

    runtime_result = DecisionRuntimeIntegration().evaluate(
        decision_id="phase6.final.decision",
        adaptive_score=adaptive_score.final_score,
        quality_score=quality_score.final_score,
    )

    assert adaptive_score.final_score > 0.8
    assert quality_score.final_score > 0.8
    assert runtime_result.final_score > 0.8
    assert runtime_result.approved is True


def test_phase_6_runtime_rejection():

    runtime_result = DecisionRuntimeIntegration().evaluate(
        decision_id="phase6.low.confidence",
        adaptive_score=0.4,
        quality_score=0.5,
    )

    assert runtime_result.final_score == 0.44
    assert runtime_result.approved is False