from uuid import UUID

from ..models.entities import (
    Portfolio,
)

from ..events.outbox import (
    OutboxMessage,
)

from ..services.portfolio_service import (
    PortfolioService,
)

from ..services.portfolio_event_dispatcher import (
    PortfolioEventDispatcher,
)



class PortfolioApplicationService:
    """
    Application layer orchestration
    for portfolio use cases.

    Responsibilities:

    - Coordinate domain services
    - Coordinate event dispatching
    - Execute application workflows

    Does NOT:

    - Contain business rules
    - Modify entities directly
    - Handle persistence
    """


    def __init__(
        self,
        portfolio_service: PortfolioService | None = None,
        event_dispatcher: PortfolioEventDispatcher | None = None,
    ):

        self.portfolio_service = (
            portfolio_service
            or PortfolioService()
        )

        self.event_dispatcher = (
            event_dispatcher
            or PortfolioEventDispatcher()
        )



    def create_portfolio(
        self,
        account_id: UUID,
        name: str,
        base_currency: str = "USD",
    ) -> tuple[
        Portfolio,
        OutboxMessage,
    ]:
        """
        Create portfolio use case.
        """


        portfolio, event = (
            self.portfolio_service.create_portfolio(
                account_id=account_id,
                name=name,
                base_currency=base_currency,
            )
        )


        message = (
            self.event_dispatcher.dispatch(
                event
            )
        )


        return portfolio, message



    def activate_portfolio(
        self,
        portfolio: Portfolio,
    ) -> OutboxMessage:
        """
        Activate portfolio use case.
        """


        event = (
            self.portfolio_service.activate_portfolio(
                portfolio
            )
        )


        return (
            self.event_dispatcher.dispatch(
                event
            )
        )



    def suspend_portfolio(
        self,
        portfolio: Portfolio,
    ) -> OutboxMessage:
        """
        Suspend portfolio use case.
        """


        event = (
            self.portfolio_service.suspend_portfolio(
                portfolio
            )
        )


        return (
            self.event_dispatcher.dispatch(
                event
            )
        )



    def close_portfolio(
        self,
        portfolio: Portfolio,
    ) -> OutboxMessage:
        """
        Close portfolio use case.
        """


        event = (
            self.portfolio_service.close_portfolio(
                portfolio
            )
        )


        return (
            self.event_dispatcher.dispatch(
                event
            )
        )