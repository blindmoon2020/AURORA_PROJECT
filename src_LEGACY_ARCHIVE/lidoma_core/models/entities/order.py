from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from lidoma_core.models.enums import (
    OrderSide,
    OrderType,
    OrderStatus,
)

from lidoma_core.models.value_objects import (
    Symbol,
    Price,
    Quantity,
)


@dataclass
class Order:
    """
    Professional trading order entity.

    Represents an instruction
    sent from strategy layer
    to execution layer.

    Supports:

    - Crypto
    - Forex
    - Stocks
    - Futures
    - Exchange integrations
    """

    symbol: Symbol

    side: OrderSide

    order_type: OrderType

    quantity: Quantity

    price: Optional[Price] = None

    status: OrderStatus = OrderStatus.CREATED


    account_id: UUID | None = None


    strategy_id: str | None = None

    signal_id: str | None = None


    venue: str | None = None

    exchange_order_id: str | None = None

    client_order_id: str | None = None


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    updated_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    metadata: dict[str, object] = field(
        default_factory=dict
    )


    def submit(self) -> None:
        """
        Submit order to execution layer.
        """

        if self.status != OrderStatus.CREATED:
            raise ValueError(
                "Only created orders can be submitted"
            )

        self.status = OrderStatus.SUBMITTED

        self._touch()


    def accept(self) -> None:
        """
        Mark order as accepted by venue.
        """

        if self.status != OrderStatus.SUBMITTED:
            raise ValueError(
                "Only submitted orders can be accepted"
            )

        self.status = OrderStatus.ACCEPTED

        self._touch()


    def fill(self) -> None:
        """
        Mark order as completely filled.
        """

        if self.status not in (
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
        ):
            raise ValueError(
                "Order cannot be filled"
            )

        self.status = OrderStatus.FILLED

        self._touch()


    def cancel(self) -> None:
        """
        Cancel active order.
        """

        if self.status in (
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ):
            raise ValueError(
                "Order cannot be cancelled"
            )

        self.status = OrderStatus.CANCELLED

        self._touch()


    def _touch(self) -> None:
        """
        Update modification timestamp.
        """

        self.updated_at = datetime.now(
            timezone.utc
        )


    def __str__(self) -> str:
        return (
            f"{self.side.value} "
            f"{self.quantity} "
            f"{self.symbol}"
        )