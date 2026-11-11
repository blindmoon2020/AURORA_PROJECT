from decimal import Decimal

from lidoma_core.models.entities import (
    Position,
    PositionStatus,
    Instrument,
    InstrumentType,
    Asset,
    AssetClass,
)

from lidoma_core.models.enums import PositionSide

from lidoma_core.models.value_objects import (
    Price,
    Quantity,
)


def create_test_instrument():

    asset = Asset(
        symbol="BTC",
        name="Bitcoin",
        asset_class=AssetClass.CRYPTO,
    )

    return Instrument(
        symbol="BTCUSDT",
        asset=asset,
        instrument_type=InstrumentType.SPOT,
        venue="BINANCE",
    )


def create_test_position():

    return Position(
        instrument=create_test_instrument(),
        side=PositionSide.LONG,
        quantity=Quantity(
            Decimal("1"),
            "BTC",
        ),
        entry_price=Price(
            Decimal("60000")
        ),
        current_price=Price(
            Decimal("60000")
        ),
    )


def test_position_creation():

    position = create_test_position()

    assert position.status == PositionStatus.OPEN

    assert (
        position.average_entry_price
        == position.entry_price
    )

    assert (
        position.remaining_quantity
        == position.quantity
    )


def test_position_update_price():

    position = create_test_position()

    position.update_price(
        Price(
            Decimal("62000")
        )
    )

    assert (
        position.current_price.value
        == Decimal("62000")
    )


def test_position_close():

    position = create_test_position()

    position.close()

    assert (
        position.status
        == PositionStatus.CLOSED
    )

    assert position.closed_at is not None


def test_position_tags():

    position = Position(
        instrument=create_test_instrument(),
        side=PositionSide.LONG,
        quantity=Quantity(
            Decimal("1"),
            "BTC",
        ),
        entry_price=Price(
            Decimal("60000")
        ),
        current_price=Price(
            Decimal("60000")
        ),
        tags=[
            " SMC ",
            "LONDON "
        ],
    )

    position.add_tag(
        "BREAKOUT"
    )

    assert "SMC" in position.tags
    assert "LONDON" in position.tags
    assert "BREAKOUT" in position.tags