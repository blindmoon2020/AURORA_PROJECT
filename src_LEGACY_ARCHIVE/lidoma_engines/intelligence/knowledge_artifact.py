from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    description: str
    source: str
    weight: float = 1.0


@dataclass(frozen=True)
class KnowledgeArtifact:
    source_id: str
    method: str
    market: str
    timeframe: str
    confidence: float
    evidence: tuple[EvidenceItem, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
