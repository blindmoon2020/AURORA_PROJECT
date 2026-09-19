from lidoma_engines import (
    DecisionContext,
    DomainEvent,
    AuditRecord,
)


def test_decision_event_audit_flow():

    context = DecisionContext(
        decision_id="decision.audit.alpha",
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

    audit = AuditRecord(
        audit_id="audit.alpha",
        entity_id=event.aggregate_id,
        action=event.event_type,
        details={
            "result": event.payload["result"]
        },
    )

    assert audit.entity_id == (
        "decision.audit.alpha"
    )

    assert audit.action == (
        "DecisionCompleted"
    )


def test_audit_timestamp_is_timezone_aware():

    audit = AuditRecord(
        audit_id="audit.time",
        entity_id="decision.time",
        action="created",
    )

    assert audit.created_at.tzinfo is not None