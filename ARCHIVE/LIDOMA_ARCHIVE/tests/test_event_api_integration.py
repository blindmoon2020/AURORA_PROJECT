from lidoma_engines import (
    DecisionContext,
    DomainEvent,
)


def test_event_and_context_integration():

    context = DecisionContext(
        decision_id="decision.event.alpha",
        market_context={
            "symbol": "BTCUSDT"
        },
    )

    event = DomainEvent(
        event_type="DecisionContextCreated",
        aggregate_id=context.decision_id,
        payload={
            "symbol": context.market_context["symbol"]
        },
    )

    assert event.aggregate_id == (
        "decision.event.alpha"
    )

    assert event.payload["symbol"] == (
        "BTCUSDT"
    )


def test_event_timestamp_is_timezone_aware():

    event = DomainEvent(
        event_type="DecisionCreated",
        aggregate_id="decision.timestamp",
    )

    assert event.created_at.tzinfo is not None