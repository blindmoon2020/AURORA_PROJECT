from lidoma_engines import (
    DecisionContext,
    DomainEvent,
    KnowledgeRecord,
    DecisionExperience,
)


def test_decision_learning_flow():

    context = DecisionContext(
        decision_id="decision.learning.alpha",
        market_context={
            "symbol": "BTCUSDT"
        },
    )

    event = DomainEvent(
        event_type="DecisionCompleted",
        aggregate_id=context.decision_id,
        payload={
            "result": "success"
        },
    )

    knowledge = KnowledgeRecord(
        knowledge_id="knowledge.learning.alpha",
        source_decision_id=event.aggregate_id,
        pattern="successful_market_pattern",
    )

    experience = DecisionExperience(
        experience_id="experience.learning.alpha",
        decision_id=knowledge.source_decision_id,
        outcome="success",
        lessons={
            "pattern": knowledge.pattern
        },
    )

    assert experience.decision_id == (
        "decision.learning.alpha"
    )

    assert experience.lessons["pattern"] == (
        "successful_market_pattern"
    )


def test_experience_timestamp_is_timezone_aware():

    experience = DecisionExperience(
        experience_id="experience.time",
        decision_id="decision.time",
        outcome="success",
    )

    assert experience.created_at.tzinfo is not None