from decimal import Decimal

from lidoma_core.models import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    Symbol,
    Quantity,
    Price,
)


def create_order():

    return Order(
        symbol=Symbol("BTCUSDT"),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Quantity(
            Decimal("0.01"),
            "BTC",
        ),
        price=Price(
            Decimal("50000"),
            "USDT",
        ),
    )


def test_order_creation():

    order = create_order()

    assert order.status == OrderStatus.CREATED

    assert str(order.symbol) == "BTCUSDT"



def test_order_lifecycle():

    order = create_order()

    order.submit()

    assert order.status == OrderStatus.SUBMITTED


    order.accept()

    assert order.status == OrderStatus.ACCEPTED


    order.fill()

    assert order.status == OrderStatus.FILLED



def test_order_cancel():

    order = create_order()

    order.cancel()

    assert order.status == OrderStatus.CANCELLED