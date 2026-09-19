from uuid import uuid4

from lidoma_core.events.idempotency import (
    EventFingerprint,
    IdempotencyRegistry,
)



def create_fingerprint():

    return EventFingerprint(

        event_id=uuid4(),

        event_type="FillCreatedEvent",

        correlation_id=uuid4(),

    )



def test_event_fingerprint_is_created():

    fingerprint = create_fingerprint()


    assert fingerprint.event_id is not None

    assert fingerprint.event_type == (
        "FillCreatedEvent"
    )

    assert fingerprint.correlation_id is not None



def test_event_fingerprint_value_is_stable():

    fingerprint = create_fingerprint()


    first_value = fingerprint.value()

    second_value = fingerprint.value()


    assert first_value == second_value



def test_unprocessed_event_returns_false():

    registry = IdempotencyRegistry()

    fingerprint = create_fingerprint()


    assert registry.is_processed(
        fingerprint
    ) is False



def test_processed_event_returns_true():

    registry = IdempotencyRegistry()

    fingerprint = create_fingerprint()


    registry.mark_processed(
        fingerprint
    )


    assert registry.is_processed(
        fingerprint
    ) is True



def test_duplicate_event_detection():

    registry = IdempotencyRegistry()

    fingerprint = create_fingerprint()


    assert registry.is_processed(
        fingerprint
    ) is False


    registry.mark_processed(
        fingerprint
    )


    assert registry.is_processed(
        fingerprint
    ) is True



def test_registry_clear_removes_processed_events():

    registry = IdempotencyRegistry()

    fingerprint = create_fingerprint()


    registry.mark_processed(
        fingerprint
    )


    assert registry.is_processed(
        fingerprint
    ) is True


    registry.clear()


    assert registry.is_processed(
        fingerprint
    ) is False