from lidoma_engines.decision.adaptive_score import (
    AdaptiveReliabilityScorer,
)


def test_adaptive_score_calculation():

    result = AdaptiveReliabilityScorer().calculate(
        source_id="source.alpha",
        historical_accuracy=1.0,
        calibration_factor=0.8,
        freshness_factor=0.9,
        governance_factor=1.0,
    )

    assert result.source_id == "source.alpha"
    assert result.final_score == 0.94


def test_adaptive_score_range():

    result = AdaptiveReliabilityScorer().calculate(
        source_id="source.beta",
        historical_accuracy=0.5,
        calibration_factor=0.5,
        freshness_factor=0.5,
        governance_factor=0.5,
    )

    assert result.final_score == 0.5


def test_invalid_source():

    try:
        AdaptiveReliabilityScorer().calculate(
            source_id="",
            historical_accuracy=0.5,
            calibration_factor=0.5,
            freshness_factor=0.5,
            governance_factor=0.5,
        )
        assert False

    except ValueError:
        assert True