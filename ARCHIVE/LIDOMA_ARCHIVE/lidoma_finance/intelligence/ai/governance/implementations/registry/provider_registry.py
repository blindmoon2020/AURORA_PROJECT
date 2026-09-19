from typing import Dict

from ...provider import ProviderIdentity


class ProviderRegistry:
    """
    Runtime registry for AI providers.

    Responsibilities:

    - Register providers
    - Retrieve providers
    - Discover available providers
    """


    def __init__(self):

        self._providers: Dict[
            str,
            ProviderIdentity
        ] = {}


    def register(
        self,
        provider: ProviderIdentity,
    ) -> None:

        self._providers[
            provider.provider_id
        ] = provider


    def get(
        self,
        provider_id: str,
    ) -> ProviderIdentity | None:

        return self._providers.get(
            provider_id
        )


    def exists(
        self,
        provider_id: str,
    ) -> bool:

        return provider_id in self._providers


    def all(
        self,
    ) -> list[ProviderIdentity]:

        return list(
            self._providers.values()
        )