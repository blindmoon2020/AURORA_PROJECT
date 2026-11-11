from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class ProviderKind(str, Enum):
    EXPERT = "expert"
    AI = "ai"
    MARKET_SOURCE = "market_source"
    NEWS_SOURCE = "news_source"
    ANALYSIS = "analysis"
    STRATEGY = "strategy"
    RISK = "risk"
    PLUGIN = "plugin"


class ProviderStatus(str, Enum):
    ACTIVE = "active"
    RESEARCH_ONLY = "research_only"
    DISCONTINUED = "discontinued"
    FUTURE = "future"


@dataclass(frozen=True)
class ProviderDescriptor:
    provider_id: str
    name: str
    kind: ProviderKind
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    status: ProviderStatus = ProviderStatus.ACTIVE
    version: str = "1"
    mandatory: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        provider_id = self.provider_id.strip().lower()
        name = self.name.strip()
        if not provider_id:
            raise ValueError("provider_id must not be empty")
        if not name:
            raise ValueError("name must not be empty")
        object.__setattr__(self, "provider_id", provider_id)
        object.__setattr__(self, "name", name)


class PluginProvider(ABC):
    @property
    @abstractmethod
    def descriptor(self) -> ProviderDescriptor:
        """Describe this replaceable provider."""


class ExpertKnowledgeProvider(PluginProvider, ABC):
    @abstractmethod
    def collect_public_knowledge(
        self,
        *,
        query: str,
        limit: int | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        """Collect legally/technically accessible public research artifacts."""


class AIProvider(PluginProvider, ABC):
    @abstractmethod
    def invoke(
        self,
        *,
        task: str,
        context: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Run a model/provider call and return structured output."""


class MarketSourceProvider(PluginProvider, ABC):
    @abstractmethod
    def fetch(
        self,
        *,
        request: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Fetch source data without leaking provider-specific schemas upstream."""


class AnalysisProvider(PluginProvider, ABC):
    @abstractmethod
    def analyze(
        self,
        *,
        data: Mapping[str, Any],
        parameters: Mapping[str, Any] | None = None,
    ) -> Mapping[str, Any]:
        """Produce a versioned analysis result from normalized inputs."""
