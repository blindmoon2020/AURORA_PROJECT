from decimal import Decimal
from uuid import uuid4

import pytest

from lidoma_core.events import (
    PortfolioCreatedEvent,
    PortfolioActivatedEvent,
    PortfolioSuspendedEvent,
    PortfolioClosedEvent,
    PortfolioAnalyticsSnapshotCreatedEvent,
)



def test_portfolio_created_event():

    portfolio_id = uuid4()

    account_id = uuid4()


    event = PortfolioCreatedEvent(

        portfolio_id=portfolio_id,

        account_id=account_id,

        name="Institutional Portfolio",

    )


    assert event.portfolio_id == portfolio_id

    assert event.account_id == account_id

    assert event.name == (
        "Institutional Portfolio"
    )

    assert event.event_type == (
        "PortfolioCreatedEvent"
    )





def test_portfolio_event_identity():

    event = PortfolioActivatedEvent(

        portfolio_id=uuid4(),

    )


    assert event.event_id is not None

    assert event.correlation_id is not None





def test_portfolio_event_immutability():

    event = PortfolioClosedEvent(

        portfolio_id=uuid4(),

    )


    with pytest.raises(
        Exception
    ):

        event.portfolio_id = uuid4()





def test_portfolio_event_metadata():

    event = PortfolioActivatedEvent(

        portfolio_id=uuid4(),

    )


    event.add_metadata(
        "source",
        "portfolio_service",
    )


    assert (
        event.metadata["source"]
        ==
        "portfolio_service"
    )





def test_portfolio_event_causation():

    first_event = PortfolioActivatedEvent(

        portfolio_id=uuid4(),

    )


    second_event = PortfolioSuspendedEvent(

        portfolio_id=uuid4(),

    )


    second_event.with_causation(
        first_event.event_id
    )


    assert (
        second_event.causation_id
        ==
        first_event.event_id
    )





def test_portfolio_analytics_snapshot_created_event():

    portfolio_id = uuid4()


    event = PortfolioAnalyticsSnapshotCreatedEvent(

        portfolio_id=portfolio_id,

        total_value=Decimal("10000"),

        currency="USDT",

        exposure=Decimal("0.75"),

        risk_score=Decimal("0.25"),

        diversification=Decimal("0.80"),

    )


    assert event.portfolio_id == portfolio_id

    assert event.total_value == Decimal("10000")

    assert event.currency == "USDT"

    assert event.exposure == Decimal("0.75")

    assert event.risk_score == Decimal("0.25")

    assert (
        event.diversification
        ==
        Decimal("0.80")
    )


    assert event.event_type == (
        "PortfolioAnalyticsSnapshotCreatedEvent"
    )





def test_all_portfolio_events_exist():

    assert PortfolioCreatedEvent is not None

    assert PortfolioActivatedEvent is not None

    assert PortfolioSuspendedEvent is not None

    assert PortfolioClosedEvent is not None

    assert PortfolioAnalyticsSnapshotCreatedEvent is not None