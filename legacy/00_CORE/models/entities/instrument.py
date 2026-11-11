from dataclasses import dataclass
from enum import Enum

from models.entities.asset import Asset


class InstrumentType(str, Enum):
    SPOT = "SPOT"
    FUTURE = "FUTURE"
    CFD = "CFD"
    OPTION = "OPTION"
    PERPETUAL = "PERPETUAL"


@dataclass(frozen=True)
class Instrument:
    """
    Tradable financial instrument.

    Examples:

    BTCUSDT Binance Spot
    EURUSD Forex CFD
    AAPL Stock
    Gold Future
    """

    symbol: str
    asset: Asset
    instrument_type: InstrumentType
    venue: str

    def __post_init__(self):

        normalized = self.symbol.upper().strip()

        if not normalized:
            raise ValueError(
                "Instrument symbol cannot be empty"
            )

        if not self.venue.strip():
            raise ValueError(
                "Venue cannot be empty"
            )

        object.__setattr__(
            self,
            "symbol",
            normalized
        )

    def __str__(self) -> str:
        return (
            f"{self.symbol} "
            f"@ {self.venue}"
        )