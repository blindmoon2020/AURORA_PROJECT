from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


from .holdings import Holdings
from ..value_objects import Money



class PortfolioStatus(str, Enum):
    """
    Lifecycle state of a portfolio.
    """

    CREATED = "CREATED"

    ACTIVE = "ACTIVE"

    SUSPENDED = "SUSPENDED"

    CLOSED = "CLOSED"




@dataclass
class Portfolio:
    """
    Core portfolio aggregate.

    Owns:

    - Lifecycle state
    - Holdings collection
    - Portfolio identity

    Designed for:

    - Risk engine
    - Allocation engine
    - Performance analytics
    - AI portfolio intelligence
    """


    account_id: UUID

    name: str

    base_currency: str = "USD"


    holdings: Holdings = field(
        default_factory=Holdings
    )


    status: PortfolioStatus = (
        PortfolioStatus.CREATED
    )


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    metadata: dict[str, object] = field(
        default_factory=dict
    )



    def activate(self) -> None:
        """
        Activate portfolio.
        """


        if self.status != PortfolioStatus.CREATED:

            raise ValueError(
                "Only created portfolios can be activated"
            )


        self.status = (
            PortfolioStatus.ACTIVE
        )



    def suspend(self) -> None:
        """
        Suspend portfolio operations.
        """


        if self.status != PortfolioStatus.ACTIVE:

            raise ValueError(
                "Only active portfolios can be suspended"
            )


        self.status = (
            PortfolioStatus.SUSPENDED
        )



    def close(self) -> None:
        """
        Close portfolio permanently.
        """


        if self.status == PortfolioStatus.CLOSED:

            raise ValueError(
                "Portfolio already closed"
            )


        self.status = (
            PortfolioStatus.CLOSED
        )



    def total_market_value(self) -> Money:
        """
        Calculate total portfolio market value.
        """


        return (
            self.holdings
            .total_market_value()
        )