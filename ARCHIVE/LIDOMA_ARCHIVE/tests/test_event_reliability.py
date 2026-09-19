from uuid import uuid4

import pytest

from lidoma_core.events import (
    DomainEvent,
    OrderCreatedEvent,
    ExecutionSubmittedEvent,
    FillCreatedEvent,
)



def test_domain_event_has_identity():

    event = DomainEvent()


    assert event.event_id is not None

    assert event.occurred_at is not None

    assert event.version == 1

    assert event.source == "lidoma_core"



def test_domain_event_type_detection():

    event = DomainEvent()


    assert event.event_type == "DomainEvent"



def test_order_created_event_inherits_domain_contract():

    event = OrderCreatedEvent(

        order_id=uuid4(),

        symbol="BTCUSDT",

        side="BUY",

        order_type="LIMIT",

        quantity="1 BTC",
    )


    assert isinstance(
        event,
        DomainEvent,
    )


    assert event.event_type == (
        "OrderCreatedEvent"
    )


    assert event.correlation_id is not None



def test_execution_event_has_traceability():

    event = ExecutionSubmittedEvent(

        execution_id=uuid4(),

        order_id=uuid4(),

        quantity="1 BTC",

        price="100 USDT",
    )


    assert isinstance(
        event.correlation_id,
        type(event.event_id),
    )


    assert event.version == 1



def test_fill_event_contract():

    event = FillCreatedEvent(

        fill_id=uuid4(),

        execution_id=uuid4(),

        quantity="0.5 BTC",

        price="101 USDT",
    )


    assert event.event_type == (
        "FillCreatedEvent"
    )


    assert event.occurred_at is not None



def test_event_metadata_can_be_extended():

    event = DomainEvent()


    event.add_metadata(
        "environment",
        "test",
    )

    event.add_metadata(
        "component",
        "execution_engine",
    )


    assert event.metadata["environment"] == (
        "test"
    )


    assert event.metadata["component"] == (
        "execution_engine"
    )



def test_event_is_immutable():

    event = DomainEvent()


    with pytest.raises(
        AttributeError
    ):

        event.version = 2