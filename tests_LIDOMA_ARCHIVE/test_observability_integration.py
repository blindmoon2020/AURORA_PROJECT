from lidoma_engines import (
    DecisionContext,
    DomainEvent,
    AuditRecord,
    ObservabilityRecord,
)


def test_audit_observability_flow():

    context = DecisionContext(
        decision_id="decision.observe.alpha",
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
        audit_id="audit.observe.alpha",
        entity_id=event.aggregate_id,
        action=event.event_type,
    )

    metric = ObservabilityRecord(
        metric_id="metric.observe.alpha",
        component="audit_engine",
        metric_type="event_count",
        value=1,
        metadata={
            "audit": audit.audit_id
        },
    )

    assert metric.component == (
        "audit_engine"
    )

    assert metric.metadata["audit"] == (
        "audit.observe.alpha"
    )


def test_observability_timestamp_is_timezone_aware():

    metric = ObservabilityRecord(
        metric_id="metric.time",
        component="system",
        metric_type="health",
        value=True,
    )

    assert metric.created_at.tzinfo is not None