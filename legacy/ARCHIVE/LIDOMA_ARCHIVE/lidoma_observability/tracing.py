from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TraceRecord:

    trace_id: str

    component: str

    operation: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.trace_id.strip():
            raise ValueError(
                "trace_id must not be empty"
            )

        if not self.component.strip():
            raise ValueError(
                "component must not be empty"
            )

        if not self.operation.strip():
            raise ValueError(
                "operation must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )