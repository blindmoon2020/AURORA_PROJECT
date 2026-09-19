from dataclasses import dataclass, field

from .contract import AIProvider


@dataclass
class AIProviderRegistry:

    providers: dict[str, AIProvider] = field(
        default_factory=dict
    )


    def register(
        self,
        provider: AIProvider,
    ):

        self.providers[
            provider.provider_id
        ] = provider


    def get(
        self,
        provider_id: str,
    ):

        return self.providers[
            provider_id
        ]


    def available(self):

        return list(
            self.providers.keys()
        )