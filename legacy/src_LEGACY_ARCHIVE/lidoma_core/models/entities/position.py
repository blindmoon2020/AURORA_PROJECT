from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Dict
from uuid import UUID, uuid4

from ..enums import PositionSide

from ..value_objects import (
    Price,
    Quantity,
    Money,
    Exposure,
)

from .instrument import Instrument



class PositionStatus(str, Enum):
    """
    Lifecycle status of a trading position.
    """

    OPEN = "OPEN"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"
    LIQUIDATED = "LIQUIDATED"




@dataclass
class Position:
    """
    Core trading position entity.

    Supports:

    - Crypto
    - Forex
    - Stocks
    - Futures
    - Commodities
    - Portfolio analytics
    - Risk calculations
    """


    instrument: Instrument

    side: PositionSide

    quantity: Quantity

    entry_price: Price

    current_price: Price


    average_entry_price: Price | None = None


    status: PositionStatus = (
        PositionStatus.OPEN
    )


    realized_quantity: Quantity | None = None


    remaining_quantity: Quantity | None = None


    strategy_id: str | None = None


    external_reference: str | None = None


    tags: list[str] = field(
        default_factory=list
    )


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    opened_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    closed_at: datetime | None = None


    metadata: Dict[str, object] = field(
        default_factory=dict
    )



    def __post_init__(self):
        """
        Initialize derived values.
        """


        if self.average_entry_price is None:

            self.average_entry_price = (
                self.entry_price
            )


        if self.remaining_quantity is None:

            self.remaining_quantity = (
                self.quantity
            )


        self.tags = [
            tag.strip()
            for tag in self.tags
            if tag.strip()
        ]



    def update_price(
        self,
        price: Price,
    ) -> None:
        """
        Update current market price.
        """


        self.current_price = price



    def market_value(self) -> Money:
        """
        Calculate current market value.

        Formula:

        quantity × current price
        """


        value = (
            self.quantity.value *
            self.current_price.value
        )


        return Money(
            amount=value,
            currency=self.current_price.currency,
        )



    def unrealized_pnl(self) -> Money:
        """
        Calculate unrealized profit/loss.

        LONG:

        Current - Entry


        SHORT:

        Entry - Current
        """


        difference = (
            self.current_price.value
            -
            self.average_entry_price.value
        )


        if self.side == PositionSide.SHORT:

            difference = -difference



        pnl = (
            difference *
            self.quantity.value
        )


        return Money(
            amount=pnl,
            currency=self.current_price.currency,
        )



    def exposure(
        self,
        portfolio_value: Decimal,
    ) -> Exposure:
        """
        Calculate position exposure ratio.

        Formula:

        Market Value / Portfolio Value
        """


        if portfolio_value <= 0:

            raise ValueError(
                "Portfolio value must be greater than zero"
            )


        ratio = (
            self.market_value().amount
            /
            portfolio_value
        )


        return Exposure(
            ratio
        )



    def close(self) -> None:
        """
        Fully close an active position.
        """


        if self.status != PositionStatus.OPEN:

            raise ValueError(
                "Only open positions can be closed"
            )


        self.status = (
            PositionStatus.CLOSED
        )


        self.closed_at = (
            datetime.now(timezone.utc)
        )



    def liquidate(self) -> None:
        """
        Mark position as liquidated.
        """


        if self.status != PositionStatus.OPEN:

            raise ValueError(
                "Only open positions can be liquidated"
            )


        self.status = (
            PositionStatus.LIQUIDATED
        )


        self.closed_at = (
            datetime.now(timezone.utc)
        )



    def add_tag(
        self,
        tag: str,
    ) -> None:
        """
        Add analytical tag.
        """


        normalized = tag.strip()


        if (
            normalized
            and normalized not in self.tags
        ):

            self.tags.append(
                normalized
            )