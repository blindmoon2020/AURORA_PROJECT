from decimal import Decimal
from uuid import uuid4

import pytest

from lidoma_core.models import (
    Execution,
    Fill,
    Price,
    Quantity,
)

from lidoma_core.models.value_objects import (
    ExecutionSummary,
)

from lidoma_core.services.execution_aggregator import (
    ExecutionAggregator,
)


def create_execution(
    quantity="1000",
):

    return Execution(
        order_id=uuid4(),

        quantity=Quantity(
            Decimal(quantity),
            "BTC",
        ),

        price=Price(
            Decimal("100"),
            "USDT",
        ),
    )



def create_fill(
    execution_id,
    quantity,
    price,
):

    return Fill(

        execution_id=execution_id,

        quantity=Quantity(
            Decimal(quantity),
            "BTC",
        ),

        price=Price(
            Decimal(price),
            "USDT",
        ),
    )



def test_execution_aggregation_success():

    execution = create_execution()

    fills = [

        create_fill(
            execution.id,
            "300",
            "100",
        ),

        create_fill(
            execution.id,
            "400",
            "101",
        ),

        create_fill(
            execution.id,
            "200",
            "99",
        ),
    ]


    summary = ExecutionAggregator().aggregate(
        execution,
        fills,
    )


    assert summary.total_quantity.value == Decimal(
        "900"
    )

    assert summary.average_price.value == Decimal(
        "100.2222222222222222222222222"
    )

    assert summary.fill_count == 3

    assert summary.completion_ratio.value == Decimal(
        "0.9"
    )



def test_execution_aggregation_rejects_empty_fills():

    execution = create_execution()


    with pytest.raises(ValueError):

        ExecutionAggregator().aggregate(
            execution,
            [],
        )



def test_execution_aggregation_rejects_wrong_execution_fill():

    execution = create_execution()


    fills = [

        create_fill(
            uuid4(),
            "100",
            "100",
        )

    ]


    with pytest.raises(ValueError):

        ExecutionAggregator().aggregate(
            execution,
            fills,
        )



def test_execution_aggregation_weighted_average_price():

    execution = create_execution()


    fills = [

        create_fill(
            execution.id,
            "900",
            "100",
        ),

        create_fill(
            execution.id,
            "100",
            "110",
        ),

    ]


    summary = ExecutionAggregator().aggregate(
        execution,
        fills,
    )


    assert summary.average_price.value == Decimal(
        "101"
    )



def test_execution_aggregation_decimal_precision():

    execution = create_execution(
        quantity="3"
    )


    fills = [

        create_fill(
            execution.id,
            "1",
            "0.1",
        ),

        create_fill(
            execution.id,
            "1",
            "0.2",
        ),

        create_fill(
            execution.id,
            "1",
            "0.3",
        ),

    ]


    summary = ExecutionAggregator().aggregate(
        execution,
        fills,
    )


    assert summary.average_price.value == Decimal(
        "0.2"
    )



def test_execution_aggregation_rejects_over_execution():

    execution = create_execution(
        quantity="100"
    )


    fills = [

        create_fill(
            execution.id,
            "150",
            "100",
        )

    ]


    with pytest.raises(ValueError):

        ExecutionAggregator().aggregate(
            execution,
            fills,
        )



def test_execution_summary_is_immutable():

    summary = ExecutionSummary(

        total_quantity=Quantity(
            Decimal("100"),
            "BTC",
        ),

        average_price=Price(
            Decimal("100"),
            "USDT",
        ),

        fill_count=1,

        completion_ratio=__import__(
            "lidoma_core.models",
            fromlist=["Percentage"]
        ).Percentage(
            Decimal("1")
        ),
    )


    with pytest.raises(
        AttributeError
    ):

        summary.average_price = Price(
            Decimal("200"),
            "USDT",
        )