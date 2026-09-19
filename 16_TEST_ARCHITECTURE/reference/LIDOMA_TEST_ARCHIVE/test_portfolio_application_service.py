from uuid import uuid4

from lidoma_core.application.portfolio_application_service import (
    PortfolioApplicationService,
)

from lidoma_core.models.entities import (
    PortfolioStatus,
)

from lidoma_core.events.outbox import (
    OutboxStatus,
)



def test_create_portfolio_application_flow():

    service = PortfolioApplicationService()


    portfolio, message = (
        service.create_portfolio(
            account_id=uuid4(),
            name="Main Portfolio",
        )
    )


    assert portfolio.name == (
        "Main Portfolio"
    )


    assert message.event_type == (
        "PortfolioCreatedEvent"
    )


    assert message.status == (
        OutboxStatus.PENDING
    )



def test_activate_portfolio_application_flow():

    service = PortfolioApplicationService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Trading Portfolio",
        )
    )


    message = (
        service.activate_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.ACTIVE
    )


    assert message.event_type == (
        "PortfolioActivatedEvent"
    )



def test_suspend_portfolio_application_flow():

    service = PortfolioApplicationService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Risk Portfolio",
        )
    )


    service.activate_portfolio(
        portfolio
    )


    message = (
        service.suspend_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.SUSPENDED
    )


    assert message.event_type == (
        "PortfolioSuspendedEvent"
    )



def test_close_portfolio_application_flow():

    service = PortfolioApplicationService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Archive Portfolio",
        )
    )


    message = (
        service.close_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.CLOSED
    )


    assert message.event_type == (
        "PortfolioClosedEvent"
    )