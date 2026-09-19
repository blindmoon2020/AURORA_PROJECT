from dataclasses import dataclass
from enum import Enum


class MarketType(str, Enum):
    """
    Global financial market categories.
    """

    CRYPTO_EXCHANGE = "CRYPTO_EXCHANGE"
    FOREX = "FOREX"
    STOCK_EXCHANGE = "STOCK_EXCHANGE"
    FUTURES_EXCHANGE = "FUTURES_EXCHANGE"
    COMMODITY_EXCHANGE = "COMMODITY_EXCHANGE"
    BOND_MARKET = "BOND_MARKET"
    ETF_MARKET = "ETF_MARKET"


class MarketSession(str, Enum):
    """
    Major global trading sessions.
    """

    SYDNEY = "SYDNEY"
    TOKYO = "TOKYO"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    GLOBAL_24_7 = "GLOBAL_24_7"


@dataclass(frozen=True)
class Market:
    """
    Core representation of a financial market.

    Examples:

    Binance Crypto Exchange
    NASDAQ Stock Exchange
    FOREX Global Market
    CME Futures Market
    """

    name: str
    market_type: MarketType
    timezone: str
    session: MarketSession

    is_24_7: bool = False

    def __post_init__(self):

        normalized = self.name.strip()

        if not normalized:
            raise ValueError(
                "Market name cannot be empty"
            )

        object.__setattr__(
            self,
            "name",
            normalized
        )

        if not self.timezone.strip():
            raise ValueError(
                "Timezone cannot be empty"
            )

    def __str__(self) -> str:
        return self.name