from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SourceReliabilityProfile:
    source_id: str
    reliability_score: float
    capability: str | None = None
    sample_size: int = 0
    last_evaluated_at: datetime | None = None
    version: str = "1"

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")

        if not 0.0 <= self.reliability_score <= 1.0:
            raise ValueError("reliability_score must be between 0 and 1")

        if self.capability is not None and not self.capability.strip():
            raise ValueError("capability must not be blank")

        if self.sample_size < 0:
            raise ValueError("sample_size must not be negative")

        if self.last_evaluated_at is not None:
            if (
                self.last_evaluated_at.tzinfo is None
                or self.last_evaluated_at.utcoffset() is None
            ):
                raise ValueError("last_evaluated_at must be timezone-aware")

        if not self.version.strip():
            raise ValueError("version must not be empty")


class ReliabilityResolver(Protocol):
    def resolve(
        self,
        source_id: str,
        capability: str,
        fallback: float,
    ) -> float:
        ...


class InMemoryReliabilityResolver:
    """
    Replaceable Phase 6.2 reliability resolver.

    Lookup order:
    1) exact source + capability profile
    2) source-wide profile
    3) evidence-provided fallback reliability
    """

    def __init__(
        self,
        profiles: tuple[SourceReliabilityProfile, ...] = (),
    ) -> None:
        self._profiles: dict[
            tuple[str, str | None],
            SourceReliabilityProfile,
        ] = {}

        for profile in profiles:
            key = (profile.source_id, profile.capability)

            if key in self._profiles:
                raise ValueError(
                    "duplicate reliability profile for "
                    f"{profile.source_id}:{profile.capability}"
                )

            self._profiles[key] = profile

    def resolve(
        self,
        source_id: str,
        capability: str,
        fallback: float,
    ) -> float:
        exact = self._profiles.get((source_id, capability))

        if exact is not None:
            return exact.reliability_score

        source_default = self._profiles.get((source_id, None))

        if source_default is not None:
            return source_default.reliability_score

        return fallback

    def all(self) -> tuple[SourceReliabilityProfile, ...]:
        return tuple(self._profiles.values())
