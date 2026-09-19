from lidoma_engines import (
    DecisionContext,
    DomainEvent,
    KnowledgeRecord,
)


def test_context_event_knowledge_flow():

    context = DecisionContext(
        decision_id="decision.knowledge.alpha",
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
        knowledge_id="knowledge.success.alpha",
        source_decision_id=event.aggregate_id,
        pattern="successful_decision_pattern",
        metadata={
            "event": event.event_type
        },
    )

    assert knowledge.source_decision_id == (
        "decision.knowledge.alpha"
    )

    assert knowledge.metadata["event"] == (
        "DecisionCompleted"
    )


def test_knowledge_timestamp_is_timezone_aware():

    knowledge = KnowledgeRecord(
        knowledge_id="knowledge.time",
        source_decision_id="decision.time",
        pattern="time_pattern",
    )

    assert knowledge.created_at.tzinfo is not None