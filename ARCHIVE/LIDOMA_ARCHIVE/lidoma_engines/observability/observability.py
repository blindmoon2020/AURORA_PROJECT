from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ObservabilityRecord:

    metric_id: str

    component: str

    metric_type: str

    value: Any

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.metric_id.strip():
            raise ValueError(
                "metric_id must not be empty"
            )

        if not self.component.strip():
            raise ValueError(
                "component must not be empty"
            )

        if not self.metric_type.strip():
            raise ValueError(
                "metric_type must not be empty"
            )