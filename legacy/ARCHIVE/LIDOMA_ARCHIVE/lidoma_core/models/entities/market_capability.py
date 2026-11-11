from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MarketCapability:
    """
    Defines trading capabilities and constraints
    of a financial market.

    Examples:

    Crypto:
        24/7 trading
        leverage supported
        short supported

    Stock:
        exchange hours
        optional short selling

    Futures:
        margin based
        contract rules
    """

    is_24_7: bool

    supports_short: bool

    supports_margin: bool

    supports_leverage: bool

    minimum_order_size: Decimal

    tick_size: Decimal

    price_precision: int


    def __post_init__(self):

        if self.minimum_order_size <= 0:
            raise ValueError(
                "Minimum order size must be positive"
            )

        if self.tick_size <= 0:
            raise ValueError(
                "Tick size must be positive"
            )

        if self.price_precision < 0:
            raise ValueError(
                "Price precision cannot be negative"
            )