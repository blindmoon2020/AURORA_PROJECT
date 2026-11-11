from lidoma_core.models import (
    Asset,
    AssetClass,
    Instrument,
    InstrumentType,
)


def test_instrument_creation():

    btc = Asset(
        symbol="BTC",
        name="Bitcoin",
        asset_class=AssetClass.CRYPTO,
    )

    instrument = Instrument(
        symbol="BTCUSDT",
        asset=btc,
        instrument_type=InstrumentType.SPOT,
        venue="BINANCE",
    )

    assert instrument.symbol == "BTCUSDT"
    assert instrument.asset == btc
    assert instrument.venue == "BINANCE"