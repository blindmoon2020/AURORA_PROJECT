from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class RiskEvent:

    event_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    event_type: str = ""

    aggregate_id: str = ""

    payload: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.event_type.strip():
            raise ValueError(
                "event_type must not be empty"
            )

        if not self.aggregate_id.strip():
            raise ValueError(
                "aggregate_id must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )