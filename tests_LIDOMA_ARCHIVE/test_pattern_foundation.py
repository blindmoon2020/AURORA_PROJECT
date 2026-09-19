from lidoma_engines.patterns import DecisionPattern


def test_decision_pattern_creation():

    pattern = DecisionPattern(
        pattern_id="pattern.alpha",
        source_experience_id="experience.alpha",
        pattern_type="market_success",
        features={
            "confidence": 0.9
        },
    )

    assert pattern.pattern_id == (
        "pattern.alpha"
    )

    assert pattern.source_experience_id == (
        "experience.alpha"
    )

    assert pattern.features["confidence"] == 0.9


def test_pattern_validation():

    try:
        DecisionPattern(
            pattern_id="",
            source_experience_id="experience.alpha",
            pattern_type="market_success",
        )

        assert False

    except ValueError:
        assert True