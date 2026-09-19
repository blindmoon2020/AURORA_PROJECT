from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PortfolioPosition:

    symbol: str
    asset_class: str

    quantity: float
    average_price: float

    currency: str

    market_value: float
    unrealized_pnl: float

    weight: float

    strategy: str | None = None


    def validate(self):

        if not self.symbol:
            raise ValueError("Symbol is required")

        if not self.asset_class:
            raise ValueError("Asset class is required")

        if self.quantity < 0:
            raise ValueError(
                "Quantity cannot be negative"
            )

        if self.average_price < 0:
            raise ValueError(
                "Average price cannot be negative"
            )

        if self.market_value < 0:
            raise ValueError(
                "Market value cannot be negative"
            )

        if self.weight < 0 or self.weight > 100:
            raise ValueError(
                "Weight must be between 0 and 100"
            )

        return True


    def to_dict(self):

        return asdict(self)


@dataclass
class PortfolioContract:

    portfolio_id: str

    base_currency: str

    positions: list[PortfolioPosition]

    cash: float

    total_equity: float

    created_at: datetime


    def validate(self):

        if not self.portfolio_id:
            raise ValueError(
                "Portfolio ID is required"
            )

        if not self.base_currency:
            raise ValueError(
                "Base currency is required"
            )

        if self.cash < 0:
            raise ValueError(
                "Cash cannot be negative"
            )

        if self.total_equity < 0:
            raise ValueError(
                "Total equity cannot be negative"
            )

        total_weight = 0.0

        for position in self.positions:

            position.validate()

            total_weight += position.weight

        if total_weight > 100.000001:
            raise ValueError(
                "Portfolio weights cannot exceed 100"
            )

        return True


    def invested_value(self):

        return sum(
            position.market_value
            for position in self.positions
        )


    def invested_weight(self):

        if self.total_equity <= 0:
            return 0.0

        return round(
            (
                self.invested_value()
                /
                self.total_equity
            ) * 100.0,
            4
        )


    def cash_weight(self):

        if self.total_equity <= 0:
            return 0.0

        return round(
            (
                self.cash
                /
                self.total_equity
            ) * 100.0,
            4
        )


    def to_dict(self):

        return {

            "portfolio_id":
                self.portfolio_id,

            "base_currency":
                self.base_currency,

            "positions":
                [
                    position.to_dict()
                    for position in self.positions
                ],

            "cash":
                self.cash,

            "total_equity":
                self.total_equity,

            "invested_value":
                self.invested_value(),

            "invested_weight":
                self.invested_weight(),

            "cash_weight":
                self.cash_weight(),

            "created_at":
                self.created_at.isoformat()

        }