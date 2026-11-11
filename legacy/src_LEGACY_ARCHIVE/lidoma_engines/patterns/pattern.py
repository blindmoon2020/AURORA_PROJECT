from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DecisionPattern:

    pattern_id: str

    source_experience_id: str

    pattern_type: str

    features: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.pattern_id.strip():
            raise ValueError(
                "pattern_id must not be empty"
            )

        if not self.source_experience_id.strip():
            raise ValueError(
                "source_experience_id must not be empty"
            )

        if not self.pattern_type.strip():
            raise ValueError(
                "pattern_type must not be empty"
            )