from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:

    provider_id: str

    reasoning: bool

    research: bool

    coding: bool

    multimodal: bool

    realtime: bool
