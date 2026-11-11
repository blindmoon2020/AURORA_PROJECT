from uuid import uuid4

from lidoma_core.events.outbox import (
    OutboxMessage,
    OutboxStatus,
    OutboxStore,
)



def create_message():

    return OutboxMessage(

        event_id=uuid4(),

        event_type="OrderCreatedEvent",

        payload={
            "order_id": "123",
            "symbol": "BTCUSDT",
        },
    )



def test_outbox_message_created():

    message = create_message()


    assert message.event_type == (
        "OrderCreatedEvent"
    )


    assert message.status == (
        OutboxStatus.PENDING
    )


    assert message.message_id is not None



def test_outbox_processing_flow():

    message = create_message()


    message.mark_processing()


    assert message.status == (
        OutboxStatus.PROCESSING
    )



def test_outbox_publish_flow():

    message = create_message()


    message.mark_processing()

    message.mark_published()


    assert message.status == (
        OutboxStatus.PUBLISHED
    )


    assert message.published_at is not None



def test_outbox_failure_retry():

    message = create_message()


    message.mark_failed()


    assert message.status == (
        OutboxStatus.FAILED
    )


    assert message.retry_count == 1



def test_outbox_store_add_message():

    store = OutboxStore()

    message = create_message()


    store.add(message)


    assert len(
        store.pending_messages()
    ) == 1



def test_outbox_store_returns_only_pending():

    store = OutboxStore()


    pending = create_message()

    published = create_message()


    published.mark_processing()

    published.mark_published()


    store.add(pending)

    store.add(published)


    messages = store.pending_messages()


    assert len(messages) == 1

    assert messages[0] == pending