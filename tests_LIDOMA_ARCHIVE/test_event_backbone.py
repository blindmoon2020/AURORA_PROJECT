from lidoma_engines.events import DomainEvent


def test_domain_event_creation():

    event = DomainEvent(
        event_type="DecisionCreated",
        aggregate_id="decision.alpha",
        payload={
            "score": 0.9
        },
    )

    assert event.event_type == (
        "DecisionCreated"
    )

    assert event.aggregate_id == (
        "decision.alpha"
    )

    assert event.payload["score"] == 0.9


def test_domain_event_validation():

    try:
        DomainEvent(
            event_type="",
            aggregate_id="decision.alpha",
        )

        assert False

    except ValueError:
        assert True