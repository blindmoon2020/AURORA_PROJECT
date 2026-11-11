from lidoma_engines import (
    DecisionExperience,
    DecisionPattern,
    DecisionAdaptation,
)


def test_pattern_to_adaptation_flow():

    experience = DecisionExperience(
        experience_id="experience.adapt.alpha",
        decision_id="decision.adapt.alpha",
        outcome="success",
    )

    pattern = DecisionPattern(
        pattern_id="pattern.adapt.alpha",
        source_experience_id=experience.experience_id,
        pattern_type="success_pattern",
    )

    adaptation = DecisionAdaptation(
        adaptation_id="adaptation.alpha",
        source_pattern_id=pattern.pattern_id,
        adjustment_type="strategy_update",
        changes={
            "confidence_threshold": 0.85
        },
    )

    assert adaptation.source_pattern_id == (
        "pattern.adapt.alpha"
    )

    assert adaptation.changes[
        "confidence_threshold"
    ] == 0.85


def test_adaptation_timestamp_is_timezone_aware():

    adaptation = DecisionAdaptation(
        adaptation_id="adaptation.time",
        source_pattern_id="pattern.time",
        adjustment_type="update",
    )

    assert adaptation.created_at.tzinfo is not None