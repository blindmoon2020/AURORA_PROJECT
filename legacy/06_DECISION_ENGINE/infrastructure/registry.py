from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .contracts import ProviderDescriptor, ProviderKind


@dataclass(frozen=True)
class RegistryEntry:
    descriptor: ProviderDescriptor
    aliases: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""

    @property
    def provider_id(self) -> str:
        return self.descriptor.provider_id


class CapabilityRegistry:
    """In-memory registry contract for the Evolution Foundation.

    Persistence/distributed discovery belongs to later phases. This object
    deliberately owns no domain entities and introduces no dependency from
    ``lidoma_core`` to external providers.
    """

    def __init__(self, entries: Iterable[RegistryEntry] | None = None) -> None:
        self._entries: dict[str, RegistryEntry] = {}
        if entries is not None:
            for entry in entries:
                self.register(entry)

    def register(self, entry: RegistryEntry, *, replace: bool = False) -> None:
        provider_id = entry.provider_id
        if provider_id in self._entries and not replace:
            raise ValueError(f"provider already registered: {provider_id}")
        self._entries[provider_id] = entry

    def get(self, provider_id: str) -> RegistryEntry:
        normalized = provider_id.strip().lower()
        try:
            return self._entries[normalized]
        except KeyError as exc:
            raise KeyError(f"provider not registered: {normalized}") from exc

    def contains(self, provider_id: str) -> bool:
        return provider_id.strip().lower() in self._entries

    def by_kind(self, kind: ProviderKind) -> tuple[RegistryEntry, ...]:
        return tuple(
            entry
            for entry in self._entries.values()
            if entry.descriptor.kind is kind
        )

    def by_capability(self, capability: str) -> tuple[RegistryEntry, ...]:
        normalized = capability.strip().lower()
        return tuple(
            entry
            for entry in self._entries.values()
            if normalized in {
                item.strip().lower() for item in entry.descriptor.capabilities
            }
        )

    def all(self) -> tuple[RegistryEntry, ...]:
        return tuple(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)
