from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderVersion:

    provider_id: str

    provider_version: str

    model_version: str

    schema_version: str