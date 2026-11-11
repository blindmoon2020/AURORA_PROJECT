from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from .provenance.provenance import ProvenanceRecord


class EvidenceDirection(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class EvidenceQuality:
    confidence: float
    reliability: float = 1.0
    weight: float = 1.0

    def __post_init__(self) -> None:
        for name, value in (
            ("confidence", self.confidence),
            ("reliability", self.reliability),
            ("weight", self.weight),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

    @property
    def effective_weight(self) -> float:
        return self.confidence * self.reliability * self.weight


@dataclass(frozen=True)
class DecisionEvidence:
    source_id: str
    capability: str
    direction: EvidenceDirection
    quality: EvidenceQuality
    reason: str
    evidence_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: ProvenanceRecord | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    dependency_keys: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")

        if not self.capability.strip():
            raise ValueError("capability must not be empty")

        if not isinstance(self.direction, EvidenceDirection):
            raise TypeError("direction must be an EvidenceDirection")

        if not self.reason.strip():
            raise ValueError("reason must not be empty")

        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")

        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        normalized_tags = tuple(tag.strip() for tag in self.tags if tag.strip())
        normalized_dependencies = tuple(
            key.strip() for key in self.dependency_keys if key.strip()
        )

        if len(set(normalized_dependencies)) != len(normalized_dependencies):
            raise ValueError("dependency_keys must not contain duplicates")

        object.__setattr__(self, "tags", normalized_tags)
        object.__setattr__(self, "dependency_keys", normalized_dependencies)

    @property
    def has_dependencies(self) -> bool:
        return bool(self.dependency_keys)


@dataclass(frozen=True)
class EvidenceAggregate:
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    bullish_weight: float
    bearish_weight: float
    neutral_weight: float
    unknown_weight: float
    direction_score: float
    agreement_ratio: float
    conflict_ratio: float
    confidence: float
    usable_evidence_count: int
    total_evidence_count: int

    def __post_init__(self) -> None:
        for name, value in (
            ("bullish_weight", self.bullish_weight),
            ("bearish_weight", self.bearish_weight),
            ("neutral_weight", self.neutral_weight),
            ("unknown_weight", self.unknown_weight),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must not be negative")

        if not -1.0 <= self.direction_score <= 1.0:
            raise ValueError("direction_score must be between -1 and 1")

        for name, value in (
            ("agreement_ratio", self.agreement_ratio),
            ("conflict_ratio", self.conflict_ratio),
            ("confidence", self.confidence),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")

        if self.usable_evidence_count < 0:
            raise ValueError("usable_evidence_count must not be negative")

        if self.total_evidence_count < 0:
            raise ValueError("total_evidence_count must not be negative")

        if self.total_evidence_count < self.usable_evidence_count:
            raise ValueError(
                "total_evidence_count must be >= usable_evidence_count"
            )
