from decimal import Decimal

from lidoma_core.models.entities import MarketCapability


def test_market_capability_creation():

    capability = MarketCapability(
        is_24_7=True,
        supports_short=True,
        supports_margin=True,
        supports_leverage=True,
        minimum_order_size=Decimal("0.001"),
        tick_size=Decimal("0.01"),
        price_precision=2,
    )

    assert capability.is_24_7 is True
    assert capability.supports_short is True
    assert capability.minimum_order_size == Decimal("0.001")


def test_market_capability_invalid_tick_size():

    try:
        MarketCapability(
            is_24_7=False,
            supports_short=False,
            supports_margin=False,
            supports_leverage=False,
            minimum_order_size=Decimal("1"),
            tick_size=Decimal("0"),
            price_precision=2,
        )

        assert False

    except ValueError:
        assert True