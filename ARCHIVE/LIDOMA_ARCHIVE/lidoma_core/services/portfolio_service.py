from uuid import UUID

from ..models.entities import (
    Portfolio,
)

from ..events import (
    PortfolioCreatedEvent,
    PortfolioActivatedEvent,
    PortfolioSuspendedEvent,
    PortfolioClosedEvent,
)

from ..events.outbox import (
    OutboxMessage,
)



class PortfolioService:
    """
    Domain service responsible for
    portfolio lifecycle orchestration.

    Responsibilities:

    - Create portfolio
    - Change portfolio lifecycle state
    - Produce domain events
    - Prepare outbox messages

    Does NOT handle:

    - Risk calculation
    - Performance calculation
    - Allocation logic
    """


    def create_portfolio(
        self,
        account_id: UUID,
        name: str,
        base_currency: str = "USD",
    ) -> tuple[
        Portfolio,
        PortfolioCreatedEvent,
    ]:

        portfolio = Portfolio(

            account_id=account_id,

            name=name,

            base_currency=base_currency,

        )


        event = PortfolioCreatedEvent(

            portfolio_id=portfolio.id,

            account_id=account_id,

            name=name,

        )


        return portfolio, event



    def activate_portfolio(
        self,
        portfolio: Portfolio,
    ) -> PortfolioActivatedEvent:


        portfolio.activate()


        return PortfolioActivatedEvent(

            portfolio_id=portfolio.id,

        )



    def suspend_portfolio(
        self,
        portfolio: Portfolio,
    ) -> PortfolioSuspendedEvent:


        portfolio.suspend()


        return PortfolioSuspendedEvent(

            portfolio_id=portfolio.id,

        )



    def close_portfolio(
        self,
        portfolio: Portfolio,
    ) -> PortfolioClosedEvent:


        portfolio.close()


        return PortfolioClosedEvent(

            portfolio_id=portfolio.id,

        )