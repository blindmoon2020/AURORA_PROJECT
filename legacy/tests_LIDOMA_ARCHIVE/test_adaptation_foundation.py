from lidoma_engines.adaptation import DecisionAdaptation


def test_decision_adaptation_creation():

    adaptation = DecisionAdaptation(
        adaptation_id="adaptation.alpha",
        source_pattern_id="pattern.alpha",
        adjustment_type="strategy_update",
        changes={
            "threshold": 0.85
        },
    )

    assert adaptation.adaptation_id == (
        "adaptation.alpha"
    )

    assert adaptation.source_pattern_id == (
        "pattern.alpha"
    )

    assert adaptation.changes["threshold"] == 0.85


def test_adaptation_validation():

    try:
        DecisionAdaptation(
            adaptation_id="",
            source_pattern_id="pattern.alpha",
            adjustment_type="strategy_update",
        )

        assert False

    except ValueError:
        assert True