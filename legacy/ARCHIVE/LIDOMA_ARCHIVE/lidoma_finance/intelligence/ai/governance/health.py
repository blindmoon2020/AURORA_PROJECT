from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderHealth:

    provider_id: str

    available: bool

    latency_ms: float