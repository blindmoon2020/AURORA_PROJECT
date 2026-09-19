from decimal import Decimal

import pytest

from lidoma_core.models import (
    Symbol,
    Price,
    Quantity,
    Money,
    Percentage,
)


def test_symbol_normalization():
    symbol = Symbol(" btcusdt ")

    assert symbol.value == "BTCUSDT"
    assert str(symbol) == "BTCUSDT"


def test_symbol_empty_rejected():
    with pytest.raises(ValueError):
        Symbol("")


def test_price_creation():
    price = Price(Decimal("65000"))

    assert price.value == Decimal("65000")
    assert price.currency == "USDT"


def test_negative_price_rejected():
    with pytest.raises(ValueError):
        Price(Decimal("-1"))


def test_quantity_creation():
    quantity = Quantity(
        Decimal("0.01"),
        "btc"
    )

    assert quantity.asset == "BTC"
    assert quantity.value == Decimal("0.01")


def test_zero_quantity_rejected():
    with pytest.raises(ValueError):
        Quantity(
            Decimal("0"),
            "BTC"
        )


def test_money_creation():
    money = Money(
        Decimal("1000")
    )

    assert money.amount == Decimal("1000")
    assert money.currency == "USDT"


def test_percentage_conversion():

    percentage = Percentage(
        Decimal("0.02")
    )

    assert percentage.as_percent() == Decimal("2")


def test_percentage_out_of_range():

    with pytest.raises(ValueError):
        Percentage(
            Decimal("1.5")
        )