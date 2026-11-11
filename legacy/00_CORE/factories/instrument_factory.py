from ..models.entities.instrument import (
    Instrument,
    InstrumentType,
)

from .asset_factory import (
    AssetFactory,
)



class InstrumentFactory:
    """
    Factory responsible for creating
    valid Instrument domain objects.
    """



    @staticmethod
    def crypto_spot(
        symbol: str,
        venue: str = "DEFAULT",
    ) -> Instrument:
        """
        Create crypto spot instrument.

        Example:

        BTCUSDT
        """



        normalized_symbol = (
            symbol
            .upper()
            .strip()
        )


        asset_symbol = (
            normalized_symbol
            .replace("USDT", "")
            .replace("USD", "")
        )


        asset = (
            AssetFactory.crypto(
                asset_symbol
            )
        )


        return Instrument(

            symbol=normalized_symbol,

            asset=asset,

            instrument_type=(
                InstrumentType.SPOT
            ),

            venue=venue,

        )
