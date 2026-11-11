from dataclasses import dataclass, field

from .contract import MarketDataProvider


@dataclass
class MarketProviderRegistry:


    providers: dict[str, MarketDataProvider] = field(
        default_factory=dict
    )


    def register(
        self,
        provider: MarketDataProvider,
    ):

        self.providers[
            provider.provider_id
        ] = provider


    def get(
        self,
        provider_id: str,
    ) -> MarketDataProvider:

        if provider_id not in self.providers:
            raise KeyError(
                f"Provider {provider_id} not found"
            )

        return self.providers[
            provider_id
        ]


    def list_providers(self):

        return list(
            self.providers.keys()
        )