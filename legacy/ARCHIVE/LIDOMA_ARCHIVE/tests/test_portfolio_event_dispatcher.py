from decimal import Decimal
from uuid import uuid4


from lidoma_core.events import (
    PortfolioCreatedEvent,
)


from lidoma_core.events.outbox import (
    OutboxStore,
    OutboxStatus,
)


from lidoma_core.services.portfolio_event_dispatcher import (
    PortfolioEventDispatcher,
)


from lidoma_core.factories import (
    PortfolioEventFactory,
)


from lidoma_core.models.value_objects import (
    Money,
    Exposure,
    RiskScore,
    DiversificationRatio,
    PortfolioAnalyticsSnapshot,
)





def create_event():

    return PortfolioCreatedEvent(

        portfolio_id=uuid4(),

        account_id=uuid4(),

        name="Dispatcher Test",

    )





def create_analytics_event():

    snapshot = PortfolioAnalyticsSnapshot(

        total_value=Money(
            Decimal("25000"),
            "USDT",
        ),

        exposure=Exposure(
            Decimal("0.50")
        ),

        risk_score=RiskScore(
            Decimal("0.20")
        ),

        diversification=DiversificationRatio(
            Decimal("0.85")
        ),

    )


    return (
        PortfolioEventFactory
        .analytics_snapshot_created(
            uuid4(),
            snapshot,
        )
    )





def test_dispatch_event_to_outbox():

    store = OutboxStore()

    dispatcher = PortfolioEventDispatcher(
        outbox_store=store
    )


    event = create_event()


    message = dispatcher.dispatch(
        event
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





def test_outbox_store_contains_message():

    store = OutboxStore()

    dispatcher = PortfolioEventDispatcher(
        outbox_store=store
    )


    dispatcher.dispatch(
        create_event()
    )


    pending = (
        store.pending_messages()
    )


    assert len(pending) == 1





def test_message_initial_status():

    dispatcher = PortfolioEventDispatcher()


    message = dispatcher.dispatch(
        create_event()
    )


    assert (
        message.status
        ==
        OutboxStatus.PENDING
    )





def test_multiple_events_dispatch():

    store = OutboxStore()

    dispatcher = PortfolioEventDispatcher(
        outbox_store=store
    )


    dispatcher.dispatch(
        create_event()
    )


    dispatcher.dispatch(
        create_event()
    )


    assert (
        len(
            store.pending_messages()
        )
        ==
        2
    )





def test_analytics_snapshot_event_dispatch_pipeline():

    store = OutboxStore()

    dispatcher = PortfolioEventDispatcher(
        outbox_store=store
    )


    event = create_analytics_event()


    message = dispatcher.dispatch(
        event
    )


    assert (
        message.event_type
        ==
        "PortfolioAnalyticsSnapshotCreatedEvent"
    )


    assert (
        message.payload["currency"]
        ==
        "USDT"
    )


    assert (
        message.payload["total_value"]
        ==
        Decimal("25000")
    )


    assert (
        len(
            store.pending_messages()
        )
        ==
        1
    )