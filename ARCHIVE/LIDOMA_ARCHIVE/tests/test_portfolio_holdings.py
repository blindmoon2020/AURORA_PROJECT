from decimal import Decimal
from uuid import uuid4


from lidoma_core.models.entities import (
    Portfolio,
    Holdings,
)

from lidoma_core.factories import (
    InstrumentFactory,
)

from lidoma_core.models.entities import (
    Position,
)

from lidoma_core.models.enums import (
    PositionSide,
)

from lidoma_core.models.value_objects import (
    Price,
    Quantity,
)



def create_position():

    instrument = InstrumentFactory.crypto_spot(
        "BTCUSDT",
        "BINANCE",
    )

    return Position(
        instrument=instrument,

        side=PositionSide.LONG,

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



def test_portfolio_has_holdings():

    portfolio = Portfolio(
        account_id=uuid4(),
        name="Main Portfolio",
    )


    assert isinstance(
        portfolio.holdings,
        Holdings,
    )



def test_add_position_to_portfolio():

    portfolio = Portfolio(
        account_id=uuid4(),
        name="Crypto Portfolio",
    )


    position = create_position()


    portfolio.holdings.add_position(
        position
    )


    assert (
        portfolio.holdings.count()
        ==
        1
    )



def test_portfolio_total_market_value():

    portfolio = Portfolio(
        account_id=uuid4(),
        name="BTC Portfolio",
    )


    portfolio.holdings.add_position(
        create_position()
    )


    value = (
        portfolio.total_market_value()
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