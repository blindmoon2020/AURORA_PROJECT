from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    source_type: str
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_reference: str | None = None
    author_or_expert_id: str | None = None
    market_scope: tuple[str, ...] = field(default_factory=tuple)
    confidence: float | None = None
    freshness_seconds: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_id = self.source_id.strip().lower()
        source_type = self.source_type.strip().lower()
        if not source_id:
            raise ValueError("source_id must not be empty")
        if not source_type:
            raise ValueError("source_type must not be empty")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.freshness_seconds is not None and self.freshness_seconds < 0:
            raise ValueError("freshness_seconds must be non-negative")
        if self.captured_at.tzinfo is None:
            raise ValueError("captured_at must be timezone-aware")
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "source_type", source_type)
