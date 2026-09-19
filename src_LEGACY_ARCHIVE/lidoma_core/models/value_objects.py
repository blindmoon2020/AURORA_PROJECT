from dataclasses import dataclass
from decimal import Decimal
from typing import Final


DEFAULT_CURRENCY: Final[str] = "USDT"



@dataclass(frozen=True)
class Currency:

    code: str


    def __post_init__(self):

        normalized = self.code.upper().strip()

        if not normalized:
            raise ValueError(
                "Currency code cannot be empty"
            )

        object.__setattr__(
            self,
            "code",
            normalized
        )


    def __str__(self):

        return self.code





@dataclass(frozen=True)
class Symbol:

    value: str


    def __post_init__(self):

        normalized = self.value.upper().strip()

        if not normalized:
            raise ValueError(
                "Symbol cannot be empty"
            )

        object.__setattr__(
            self,
            "value",
            normalized
        )


    def __str__(self):

        return self.value





@dataclass(frozen=True)
class Price:

    value: Decimal

    currency: str = DEFAULT_CURRENCY


    def __post_init__(self):

        if self.value <= 0:

            raise ValueError(
                "Price must be greater than zero"
            )


        object.__setattr__(
            self,
            "currency",
            self.currency.upper()
        )


    def __str__(self):

        return f"{self.value} {self.currency}"





@dataclass(frozen=True)
class Quantity:

    value: Decimal

    asset: str


    def __post_init__(self):

        if self.value <= 0:

            raise ValueError(
                "Quantity must be greater than zero"
            )


        normalized = self.asset.upper().strip()


        if not normalized:

            raise ValueError(
                "Asset cannot be empty"
            )


        object.__setattr__(
            self,
            "asset",
            normalized
        )


    def __str__(self):

        return f"{self.value} {self.asset}"





@dataclass(frozen=True)
class Money:

    amount: Decimal

    currency: str = DEFAULT_CURRENCY


    def __post_init__(self):

        object.__setattr__(
            self,
            "currency",
            self.currency.upper()
        )


    def __str__(self):

        return f"{self.amount} {self.currency}"





@dataclass(frozen=True)
class Percentage:

    value: Decimal


    def __post_init__(self):

        if self.value < 0 or self.value > 1:

            raise ValueError(
                "Percentage must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.value *
            Decimal("100")
        )





@dataclass(frozen=True)
class Exposure:

    value: Decimal


    def __post_init__(self):

        if self.value < 0 or self.value > 1:

            raise ValueError(
                "Exposure must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.value *
            Decimal("100")
        )





@dataclass(frozen=True)
class Allocation:

    weight: Decimal


    def __post_init__(self):

        if self.weight < 0 or self.weight > 1:

            raise ValueError(
                "Allocation must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.weight *
            Decimal("100")
        )





@dataclass(frozen=True)
class Concentration:

    value: Decimal


    def __post_init__(self):

        if self.value < 0 or self.value > 1:

            raise ValueError(
                "Concentration must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.value *
            Decimal("100")
        )





@dataclass(frozen=True)
class RiskScore:

    value: Decimal


    def __post_init__(self):

        if self.value < 0 or self.value > 1:

            raise ValueError(
                "Risk score must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.value *
            Decimal("100")
        )





@dataclass(frozen=True)
class DiversificationRatio:

    value: Decimal


    def __post_init__(self):

        if self.value < 0 or self.value > 1:

            raise ValueError(
                "Diversification ratio must be between 0 and 1"
            )


    def as_percent(self):

        return (
            self.value *
            Decimal("100")
        )





@dataclass(frozen=True)
class PortfolioAnalyticsSnapshot:

    total_value: Money

    exposure: Exposure

    risk_score: RiskScore

    diversification: DiversificationRatio





@dataclass(frozen=True)
class ExecutionSummary:

    total_quantity: Quantity

    average_price: Price

    fill_count: int

    completion_ratio: Percentage


    def __post_init__(self):

        if self.fill_count <= 0:

            raise ValueError(
                "Fill count must be greater than zero"
            )