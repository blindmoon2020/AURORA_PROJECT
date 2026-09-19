from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditRecord:

    audit_id: str

    entity_id: str

    action: str

    details: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.audit_id.strip():
            raise ValueError(
                "audit_id must not be empty"
            )

        if not self.entity_id.strip():
            raise ValueError(
                "entity_id must not be empty"
            )

        if not self.action.strip():
            raise ValueError(
                "action must not be empty"
            )