from lidoma_engines import (
    DecisionExperience,
    DecisionPattern,
    KnowledgeRecord,
)


def test_experience_to_pattern_flow():

    knowledge = KnowledgeRecord(
        knowledge_id="knowledge.pattern.alpha",
        source_decision_id="decision.pattern.alpha",
        pattern="successful_trade_pattern",
    )

    experience = DecisionExperience(
        experience_id="experience.pattern.alpha",
        decision_id=knowledge.source_decision_id,
        outcome="success",
        lessons={
            "pattern": knowledge.pattern
        },
    )

    pattern = DecisionPattern(
        pattern_id="pattern.alpha",
        source_experience_id=experience.experience_id,
        pattern_type="success_detection",
        features={
            "outcome": experience.outcome
        },
    )

    assert pattern.source_experience_id == (
        "experience.pattern.alpha"
    )

    assert pattern.features["outcome"] == (
        "success"
    )


def test_pattern_timestamp_is_timezone_aware():

    pattern = DecisionPattern(
        pattern_id="pattern.time",
        source_experience_id="experience.time",
        pattern_type="time_pattern",
    )

    assert pattern.created_at.tzinfo is not None