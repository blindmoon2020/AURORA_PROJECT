from decimal import Decimal
from uuid import uuid4


from lidoma_core.factories import (
    AssetFactory,
    InstrumentFactory,
    PortfolioEventFactory,
)


from lidoma_core.models.entities.asset import (
    AssetClass,
)


from lidoma_core.models.entities.instrument import (
    InstrumentType,
)


from lidoma_core.models.value_objects import (
    Money,
    Exposure,
    RiskScore,
    DiversificationRatio,
    PortfolioAnalyticsSnapshot,
)





def test_crypto_asset_factory():

    asset = (
        AssetFactory.crypto(
            "btc"
        )
    )


    assert asset.symbol == "BTC"

    assert asset.name == "BTC"

    assert (
        asset.asset_class
        ==
        AssetClass.CRYPTO
    )





def test_crypto_asset_factory_custom_name():

    asset = (
        AssetFactory.crypto(
            "eth",
            "Ethereum",
        )
    )


    assert asset.symbol == "ETH"

    assert asset.name == "Ethereum"





def test_crypto_spot_instrument_factory():

    instrument = (
        InstrumentFactory.crypto_spot(
            "BTCUSDT",
            "BINANCE",
        )
    )


    assert (
        instrument.symbol
        ==
        "BTCUSDT"
    )


    assert (
        instrument.asset.symbol
        ==
        "BTC"
    )


    assert (
        instrument.instrument_type
        ==
        InstrumentType.SPOT
    )


    assert (
        instrument.venue
        ==
        "BINANCE"
    )





def test_portfolio_event_factory():

    portfolio_id = uuid4()


    snapshot = PortfolioAnalyticsSnapshot(

        total_value=Money(
            Decimal("10000"),
            "USDT",
        ),

        exposure=Exposure(
            Decimal("0.60")
        ),

        risk_score=RiskScore(
            Decimal("0.20")
        ),

        diversification=DiversificationRatio(
            Decimal("0.80")
        ),

    )


    event = (
        PortfolioEventFactory
        .analytics_snapshot_created(
            portfolio_id,
            snapshot,
        )
    )


    assert (
        event.portfolio_id
        ==
        portfolio_id
    )


    assert (
        event.total_value
        ==
        Decimal("10000")
    )


    assert event.currency == "USDT"


    assert (
        event.exposure
        ==
        Decimal("0.60")
    )


    assert (
        event.risk_score
        ==
        Decimal("0.20")
    )


    assert (
        event.diversification
        ==
        Decimal("0.80")
    )