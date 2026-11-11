from ..models.entities.asset import (
    Asset,
    AssetClass,
)



class AssetFactory:
    """
    Factory responsible for creating
    valid Asset domain objects.

    Centralizes asset creation rules.
    """



    @staticmethod
    def crypto(
        symbol: str,
        name: str | None = None,
    ) -> Asset:
        """
        Create cryptocurrency asset.
        """


        normalized_symbol = (
            symbol
            .upper()
            .strip()
        )


        return Asset(

            symbol=normalized_symbol,

            name=(
                name
                or normalized_symbol
            ),

            asset_class=(
                AssetClass.CRYPTO
            ),

        )