from decimal import Decimal

from lidoma_core.factories import InstrumentFactory

from lidoma_core.models.entities import (
    Holdings,
    Position,
)

from lidoma_core.models.enums import PositionSide

from lidoma_core.models.value_objects import (
    Price,
    Quantity,
)



def create_position(
    quantity="2",
    price="60000",
):

    instrument = InstrumentFactory.crypto_spot(
        "BTCUSDT",
        "BINANCE",
    )


    return Position(

        instrument=instrument,

        side=PositionSide.LONG,

        quantity=Quantity(
            Decimal(quantity),
            "BTC",
        ),

        entry_price=Price(
            Decimal("50000"),
            "USDT",
        ),

        current_price=Price(
            Decimal(price),
            "USDT",
        ),
    )



def test_concentration():

    holdings = Holdings()

    position = create_position()

    holdings.add_position(
        position
    )


    concentration = (
        holdings.concentration(
            position.id
        )
    )


    assert (
        concentration.value
        ==
        Decimal("1")
    )



def test_diversification_ratio():

    holdings = Holdings()

    position = create_position()

    holdings.add_position(
        position
    )


    diversification = (
        holdings.diversification_ratio()
    )


    assert (
        diversification.value
        ==
        Decimal("0")
    )



def test_risk_score():

    holdings = Holdings()

    position = create_position()

    holdings.add_position(
        position
    )


    score = holdings.risk_score()


    assert (
        score.value
        ==
        Decimal("1")
    )