from decimal import Decimal


from lidoma_core.factories import (
    InstrumentFactory,
)

from lidoma_core.models.entities.position import (
    Position,
)

from lidoma_core.models.enums import (
    PositionSide,
)

from lidoma_core.models.value_objects import (
    Price,
    Quantity,
)



def create_position(
    side=PositionSide.LONG,
):

    instrument = (
        InstrumentFactory.crypto_spot(
            "BTCUSDT",
            "BINANCE",
        )
    )


    return Position(

        instrument=instrument,

        side=side,

        quantity=Quantity(
            Decimal("2"),
            "BTC",
        ),

        entry_price=Price(
            Decimal("50000"),
            "USDT",
        ),

        current_price=Price(
            Decimal("60000"),
            "USDT",
        ),
    )



def test_market_value_calculation():

    position = create_position()


    value = (
        position.market_value()
    )


    assert (
        value.amount
        ==
        Decimal("120000")
    )


    assert (
        value.currency
        ==
        "USDT"
    )



def test_long_unrealized_pnl():

    position = create_position(
        PositionSide.LONG
    )


    pnl = (
        position.unrealized_pnl()
    )


    assert (
        pnl.amount
        ==
        Decimal("20000")
    )



def test_short_unrealized_pnl():

    position = create_position(
        PositionSide.SHORT
    )


    pnl = (
        position.unrealized_pnl()
    )


    assert (
        pnl.amount
        ==
        Decimal("-20000")
    )



def test_position_exposure():

    position = create_position()


    exposure = (
        position.exposure(
            Decimal("240000")
        )
    )


    assert (
        exposure.value
        ==
        Decimal("0.5")
    )