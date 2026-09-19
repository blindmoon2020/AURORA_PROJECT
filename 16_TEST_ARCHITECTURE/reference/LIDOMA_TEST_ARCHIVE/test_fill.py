from decimal import Decimal
from uuid import uuid4

from lidoma_core.models import (
    Fill,
    Quantity,
    Price,
)


def create_fill():

    return Fill(
        execution_id=uuid4(),

        quantity=Quantity(
            Decimal("10"),
            "AAPL",
        ),

        price=Price(
            Decimal("200"),
            "USD",
        ),
    )


def test_fill_creation():

    fill = create_fill()

    assert fill.quantity.value == Decimal("10")

    assert fill.quantity.asset == "AAPL"

    assert fill.price.value == Decimal("200")

    assert fill.price.currency == "USD"



def test_fill_has_execution_reference():

    execution_id = uuid4()

    fill = Fill(
        execution_id=execution_id,

        quantity=Quantity(
            Decimal("1"),
            "BTC",
        ),

        price=Price(
            Decimal("60000"),
            "USD",
        ),
    )

    assert fill.execution_id == execution_id