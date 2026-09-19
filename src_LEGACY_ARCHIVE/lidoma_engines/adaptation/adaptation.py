from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DecisionAdaptation:

    adaptation_id: str

    source_pattern_id: str

    adjustment_type: str

    changes: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.adaptation_id.strip():
            raise ValueError(
                "adaptation_id must not be empty"
            )

        if not self.source_pattern_id.strip():
            raise ValueError(
                "source_pattern_id must not be empty"
            )

        if not self.adjustment_type.strip():
            raise ValueError(
                "adjustment_type must not be empty"
            )