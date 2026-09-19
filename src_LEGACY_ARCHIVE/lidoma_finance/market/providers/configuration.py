from dataclasses import dataclass


@dataclass(frozen=True)
class MarketProviderConfiguration:

    provider_id: str

    name: str

    environment: str

    enabled: bool = True


    def __post_init__(self):

        if not self.provider_id.strip():
            raise ValueError(
                "provider_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "provider name must not be empty"
            )

        if not self.environment.strip():
            raise ValueError(
                "environment must not be empty"
            )