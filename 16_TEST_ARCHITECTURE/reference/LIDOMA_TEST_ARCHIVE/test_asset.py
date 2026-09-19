from lidoma_core.models import Asset, AssetClass


def test_asset_creation():

    btc = Asset(
        symbol="btc",
        name="Bitcoin",
        asset_class=AssetClass.CRYPTO,
    )

    assert btc.symbol == "BTC"
    assert btc.asset_class == AssetClass.CRYPTO