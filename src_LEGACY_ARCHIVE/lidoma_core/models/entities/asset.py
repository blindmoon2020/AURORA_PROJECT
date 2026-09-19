from dataclasses import dataclass
from enum import Enum


class AssetClass(str, Enum):
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    STOCK = "STOCK"
    INDEX = "INDEX"
    COMMODITY = "COMMODITY"
    BOND = "BOND"
    ETF = "ETF"
    FUTURE = "FUTURE"


@dataclass(frozen=True)
class Asset:
    """
    Core representation of a financial asset.

    Examples:
    BTC
    EUR
    AAPL
    GOLD
    US10Y
    """

    symbol: str
    name: str
    asset_class: AssetClass

    def __post_init__(self):
        normalized = self.symbol.upper().strip()

        if not normalized:
            raise ValueError("Asset symbol cannot be empty")

        object.__setattr__(
            self,
            "symbol",
            normalized
        )

    def __str__(self) -> str:
        return self.symbol