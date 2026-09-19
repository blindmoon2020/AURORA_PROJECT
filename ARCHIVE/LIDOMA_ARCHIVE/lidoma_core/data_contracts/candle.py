from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:

    symbol: str

    open: float

    high: float

    low: float

    close: float

    volume: float

    timestamp: datetime


    def __post_init__(self):

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if self.open < 0:
            raise ValueError(
                "open must be >= 0"
            )

        if self.high < 0:
            raise ValueError(
                "high must be >= 0"
            )

        if self.low < 0:
            raise ValueError(
                "low must be >= 0"
            )

        if self.close < 0:
            raise ValueError(
                "close must be >= 0"
            )

        if self.volume < 0:
            raise ValueError(
                "volume must be >= 0"
            )

        if (
            self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )