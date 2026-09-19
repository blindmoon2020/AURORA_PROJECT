from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FundingRate:

    symbol: str

    rate: float

    timestamp: datetime


    def __post_init__(self):

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if (
            self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )