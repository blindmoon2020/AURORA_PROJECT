from uuid import uuid4

import pytest

from lidoma_core.services.portfolio_service import (
    PortfolioService,
)

from lidoma_core.models.entities import (
    PortfolioStatus,
)

from lidoma_core.events import (
    PortfolioCreatedEvent,
    PortfolioActivatedEvent,
    PortfolioSuspendedEvent,
    PortfolioClosedEvent,
)



def test_create_portfolio():

    service = PortfolioService()

    account_id = uuid4()


    portfolio, event = (
        service.create_portfolio(
            account_id=account_id,
            name="Core Portfolio",
        )
    )


    assert portfolio.account_id == account_id

    assert portfolio.name == (
        "Core Portfolio"
    )

    assert isinstance(
        event,
        PortfolioCreatedEvent,
    )

    assert event.portfolio_id == portfolio.id



def test_activate_portfolio():

    service = PortfolioService()

    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Trading Portfolio",
        )
    )


    event = (
        service.activate_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.ACTIVE
    )


    assert isinstance(
        event,
        PortfolioActivatedEvent,
    )



def test_suspend_portfolio():

    service = PortfolioService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Risk Portfolio",
        )
    )


    service.activate_portfolio(
        portfolio
    )


    event = (
        service.suspend_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.SUSPENDED
    )


    assert isinstance(
        event,
        PortfolioSuspendedEvent,
    )



def test_close_portfolio():

    service = PortfolioService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Archive Portfolio",
        )
    )


    event = (
        service.close_portfolio(
            portfolio
        )
    )


    assert (
        portfolio.status
        ==
        PortfolioStatus.CLOSED
    )


    assert isinstance(
        event,
        PortfolioClosedEvent,
    )



def test_invalid_activation():

    service = PortfolioService()


    portfolio, _ = (
        service.create_portfolio(
            uuid4(),
            "Invalid Flow",
        )
    )


    service.activate_portfolio(
        portfolio
    )


    with pytest.raises(ValueError):

        service.activate_portfolio(
            portfolio
        )