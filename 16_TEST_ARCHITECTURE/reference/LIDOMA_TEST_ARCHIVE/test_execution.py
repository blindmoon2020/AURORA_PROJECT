from decimal import Decimal
from uuid import uuid4

from lidoma_core.models import (
    Execution,
    ExecutionStatus,
    Quantity,
    Price,
)


def create_execution():

    return Execution(
        order_id=uuid4(),

        quantity=Quantity(
            Decimal("1"),
            "UNIT",
        ),

        price=Price(
            Decimal("100"),
            "USD",
        ),
    )


def test_execution_creation():

    execution = create_execution()

    assert execution.status == ExecutionStatus.CREATED

    assert execution.quantity.value == Decimal("1")

    assert execution.price.value == Decimal("100")



def test_execution_lifecycle():

    execution = create_execution()

    execution.submit()

    assert execution.status == ExecutionStatus.SUBMITTED


    execution.complete()

    assert execution.status == ExecutionStatus.COMPLETED



def test_execution_failure():

    execution = create_execution()

    execution.fail()

    assert execution.status == ExecutionStatus.FAILED