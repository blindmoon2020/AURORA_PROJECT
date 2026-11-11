from decimal import Decimal
from uuid import uuid4

import pytest

from lidoma_core.events import (
    PortfolioCreatedEvent,
    PortfolioAnalyticsSnapshotCreatedEvent,
)

from lidoma_core.events.outbox import (
    OutboxMessage,
)

from lidoma_core.services.event_outbox_mapper import (
    EventOutboxMapper,
)



def test_event_mapping_to_outbox():

    mapper = EventOutboxMapper()


    event = PortfolioCreatedEvent(

        portfolio_id=uuid4(),

        account_id=uuid4(),

        name="Core Portfolio",

    )


    message = mapper.map(
        event
    )


    assert isinstance(
        message,
        OutboxMessage,
    )


    assert (
        message.event_id
        ==
        event.event_id
    )


    assert (
        message.event_type
        ==
        "PortfolioCreatedEvent"
    )





def test_payload_contains_event_data():

    mapper = EventOutboxMapper()


    portfolio_id = uuid4()

    account_id = uuid4()


    event = PortfolioCreatedEvent(

        portfolio_id=portfolio_id,

        account_id=account_id,

        name="Institutional",

    )


    message = mapper.map(
        event
    )


    assert (
        message.payload["name"]
        ==
        "Institutional"
    )


    assert (
        message.payload["portfolio_id"]
        ==
        str(portfolio_id)
    )





def test_mapper_rejects_invalid_input():

    mapper = EventOutboxMapper()


    with pytest.raises(
        TypeError
    ):

        mapper.map(
            "invalid event"
        )





def test_event_type_preservation():

    mapper = EventOutboxMapper()


    event = PortfolioCreatedEvent(

        portfolio_id=uuid4(),

        account_id=uuid4(),

        name="Test",

    )


    message = mapper.map(
        event
    )


    assert (
        message.payload["event_type"]
        ==
        "PortfolioCreatedEvent"
    )





def test_outbox_message_initial_state():

    mapper = EventOutboxMapper()


    event = PortfolioCreatedEvent(

        portfolio_id=uuid4(),

        account_id=uuid4(),

        name="Audit",

    )


    message = mapper.map(
        event
    )


    assert (
        message.status.value
        ==
        "PENDING"
    )





def test_analytics_snapshot_event_mapping():

    mapper = EventOutboxMapper()


    portfolio_id = uuid4()


    event = PortfolioAnalyticsSnapshotCreatedEvent(

        portfolio_id=portfolio_id,

        total_value=Decimal("50000"),

        currency="USDT",

        exposure=Decimal("0.70"),

        risk_score=Decimal("0.30"),

        diversification=Decimal("0.85"),

    )


    message = mapper.map(
        event
    )


    assert (
        message.event_type
        ==
        "PortfolioAnalyticsSnapshotCreatedEvent"
    )


    assert (
        message.payload["portfolio_id"]
        ==
        str(portfolio_id)
    )


    assert (
        message.payload["total_value"]
        ==
        Decimal("50000")
    )


    assert (
        message.payload["currency"]
        ==
        "USDT"
    )


    assert (
        message.payload["risk_score"]
        ==
        Decimal("0.30")
    )