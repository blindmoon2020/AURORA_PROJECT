from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class MarketData:

    symbol: str

    price: float

    volume: float

    timeframe: str

    timestamp: datetime


    def __post_init__(self):

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if self.price < 0:
            raise ValueError(
                "price must be positive"
            )

        if (
            self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )