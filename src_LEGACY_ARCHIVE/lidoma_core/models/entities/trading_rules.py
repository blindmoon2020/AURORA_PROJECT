from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradingRules:
    """
    Defines basic trading constraints
    for a tradable instrument.

    Examples:

    Crypto:
        BTCUSDT quantity rules

    Forex:
        Lot and precision rules

    Stocks:
        Price increment rules
    """

    minimum_quantity: Decimal

    maximum_quantity: Decimal | None

    tick_size: Decimal

    price_precision: int

    quantity_precision: int

    lot_size: Decimal | None = None

    contract_size: Decimal | None = None

    supports_fractional: bool = False


    def __post_init__(self):

        if self.minimum_quantity <= 0:
            raise ValueError(
                "Minimum quantity must be positive"
            )

        if self.maximum_quantity is not None:

            if self.maximum_quantity <= 0:
                raise ValueError(
                    "Maximum quantity must be positive"
                )

            if self.maximum_quantity < self.minimum_quantity:
                raise ValueError(
                    "Maximum quantity cannot be smaller than minimum quantity"
                )

        if self.tick_size <= 0:
            raise ValueError(
                "Tick size must be positive"
            )

        if self.price_precision < 0:
            raise ValueError(
                "Price precision cannot be negative"
            )

        if self.quantity_precision < 0:
            raise ValueError(
                "Quantity precision cannot be negative"
            )

        if self.lot_size is not None and self.lot_size <= 0:
            raise ValueError(
                "Lot size must be positive"
            )

        if self.contract_size is not None and self.contract_size <= 0:
            raise ValueError(
                "Contract size must be positive"
            )