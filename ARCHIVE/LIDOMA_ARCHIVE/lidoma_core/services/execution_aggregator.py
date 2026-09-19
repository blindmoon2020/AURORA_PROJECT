from decimal import Decimal
from typing import Sequence

from ..models.entities import (
    Execution,
    Fill,
)

from ..models.value_objects import (
    ExecutionSummary,
    Price,
    Quantity,
    Percentage,
)


class ExecutionAggregator:
    """
    Domain service responsible for
    aggregating execution fills.

    Converts multiple fills into
    execution intelligence metrics.

    Responsibilities:

    - Validate execution ownership
    - Validate execution quantity integrity
    - Calculate executed quantity
    - Calculate weighted average price
    - Calculate completion ratio
    - Produce immutable execution summary
    """

    def aggregate(
        self,
        execution: Execution,
        fills: Sequence[Fill],
    ) -> ExecutionSummary:
        """
        Aggregate fills into execution summary.
        """

        if not fills:
            raise ValueError(
                "Cannot aggregate empty fills"
            )


        for fill in fills:

            if fill.execution_id != execution.id:
                raise ValueError(
                    "Fill does not belong to execution"
                )


        total_quantity_value = sum(
            (
                fill.quantity.value
                for fill in fills
            ),
            Decimal("0"),
        )


        if total_quantity_value <= 0:
            raise ValueError(
                "Total executed quantity must be greater than zero"
            )


        if total_quantity_value > execution.quantity.value:
            raise ValueError(
                "Executed quantity cannot exceed requested quantity"
            )


        weighted_price_value = sum(
            (
                fill.quantity.value *
                fill.price.value
                for fill in fills
            ),
            Decimal("0"),
        )


        average_price_value = (
            weighted_price_value /
            total_quantity_value
        )


        completion_ratio_value = (
            total_quantity_value /
            execution.quantity.value
        )


        return ExecutionSummary(

            total_quantity=Quantity(
                total_quantity_value,
                execution.quantity.asset,
            ),

            average_price=Price(
                average_price_value,
                execution.price.currency,
            ),

            fill_count=len(fills),

            completion_ratio=Percentage(
                completion_ratio_value
            ),
        )