from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class OrderBook:

    symbol: str

    bids: list[dict[str, Any]]

    asks: list[dict[str, Any]]

    timestamp: datetime


    def __post_init__(self):

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if self.bids is None:
            raise ValueError(
                "bids must not be None"
            )

        if self.asks is None:
            raise ValueError(
                "asks must not be None"
            )

        if (
            self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )