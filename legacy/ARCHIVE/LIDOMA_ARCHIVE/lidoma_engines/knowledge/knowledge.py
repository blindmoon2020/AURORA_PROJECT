from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class KnowledgeRecord:

    knowledge_id: str

    source_decision_id: str

    pattern: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.knowledge_id.strip():
            raise ValueError(
                "knowledge_id must not be empty"
            )

        if not self.source_decision_id.strip():
            raise ValueError(
                "source_decision_id must not be empty"
            )

        if not self.pattern.strip():
            raise ValueError(
                "pattern must not be empty"
            )