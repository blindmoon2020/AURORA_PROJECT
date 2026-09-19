from lidoma_engines.decision.runtime import (
    DecisionRuntimeIntegration,
)


def test_runtime_integration_approval():

    result = DecisionRuntimeIntegration().evaluate(
        decision_id="decision.runtime.alpha",
        adaptive_score=0.9,
        quality_score=0.8,
    )

    assert result.final_score == 0.86
    assert result.approved is True
    assert result.reason == (
        "phase_6_runtime_integration"
    )


def test_runtime_integration_rejection():

    result = DecisionRuntimeIntegration().evaluate(
        decision_id="decision.runtime.beta",
        adaptive_score=0.5,
        quality_score=0.4,
    )

    assert result.final_score == 0.46
    assert result.approved is False


def test_runtime_invalid_id():

    try:
        DecisionRuntimeIntegration().evaluate(
            decision_id="",
            adaptive_score=0.5,
            quality_score=0.5,
        )

        assert False

    except ValueError:
        assert True