from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from .position import Position

from ..value_objects import (
    Money,
    Allocation,
    Exposure,
    Concentration,
    DiversificationRatio,
    RiskScore,
)



@dataclass
class Holdings:
    """
    Portfolio holdings collection.

    Responsibilities:

    - Manage positions
    - Calculate market value
    - Calculate allocations
    - Calculate exposure
    - Calculate concentration
    - Calculate diversification
    - Produce risk foundation metrics
    """


    _positions: dict[UUID, Position] = field(
        default_factory=dict
    )



    def add_position(
        self,
        position: Position,
    ) -> None:


        if position.id in self._positions:

            raise ValueError(
                "Position already exists"
            )


        self._positions[position.id] = position




    def remove_position(
        self,
        position_id: UUID,
    ) -> Position:


        if position_id not in self._positions:

            raise ValueError(
                "Position not found"
            )


        return self._positions.pop(
            position_id
        )




    def get_position(
        self,
        position_id: UUID,
    ) -> Position:


        if position_id not in self._positions:

            raise ValueError(
                "Position not found"
            )


        return self._positions[position_id]




    def all_positions(
        self,
    ) -> list[Position]:

        return list(
            self._positions.values()
        )




    def count(
        self,
    ) -> int:

        return len(
            self._positions
        )




    def total_market_value(
        self,
    ) -> Money:


        if not self._positions:

            return Money(
                Decimal("0")
            )


        values = [

            position.market_value()

            for position in self._positions.values()

        ]


        total = sum(

            (
                value.amount
                for value in values
            ),

            Decimal("0")

        )


        return Money(
            amount=total,
            currency=values[0].currency,
        )




    def position_allocation(
        self,
        position_id: UUID,
    ) -> Allocation:


        position = self.get_position(
            position_id
        )


        total = self.total_market_value()


        if total.amount <= 0:

            raise ValueError(
                "Cannot calculate allocation"
            )


        return Allocation(

            position.market_value().amount
            /
            total.amount

        )




    def total_exposure(
        self,
    ) -> Exposure:


        total = self.total_market_value()


        if total.amount <= 0:

            return Exposure(
                Decimal("0")
            )


        return Exposure(
            Decimal("1")
        )




    def concentration(
        self,
        position_id: UUID,
    ) -> Concentration:
        """
        Largest position dominance.

        Formula:

        Position Value / Total Portfolio Value
        """


        allocation = self.position_allocation(
            position_id
        )


        return Concentration(
            allocation.weight
        )




    def diversification_ratio(
        self,
    ) -> DiversificationRatio:
        """
        Simple diversification metric.

        Higher number means
        better distribution.

        Formula:

        1 - largest concentration
        """


        if not self._positions:

            return DiversificationRatio(
                Decimal("0")
            )


        concentrations = [

            self.concentration(
                position.id
            ).value

            for position
            in self._positions.values()

        ]


        maximum = max(
            concentrations
        )


        return DiversificationRatio(
            Decimal("1") - maximum
        )




    def risk_score(
        self,
    ) -> RiskScore:
        """
        Basic portfolio risk score.

        Based on concentration.

        Higher concentration
        increases risk.
        """


        if not self._positions:

            return RiskScore(
                Decimal("0")
            )


        diversification = (
            self.diversification_ratio()
        )


        return RiskScore(
            Decimal("1")
            -
            diversification.value
        )