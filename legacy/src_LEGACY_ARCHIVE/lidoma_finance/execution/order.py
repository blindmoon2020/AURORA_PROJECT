from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


OrderSide = Literal[
    "BUY",
    "SELL",
]


@dataclass(frozen=True)
class TradeOrder:

    order_id: str

    symbol: str

    side: OrderSide

    quantity: float

    price: float

    created_at: datetime


    def __post_init__(self):

        if not self.order_id.strip():
            raise ValueError(
                "order_id must not be empty"
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if self.quantity <= 0:
            raise ValueError(
                "quantity must be positive"
            )

        if self.price < 0:
            raise ValueError(
                "price cannot be negative"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )