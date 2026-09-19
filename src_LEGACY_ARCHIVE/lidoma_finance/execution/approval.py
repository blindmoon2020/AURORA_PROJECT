from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ExecutionApproval:

    approval_id: str

    decision_id: str

    approved: bool

    reason: str

    created_at: datetime


    def __post_init__(self):

        if not self.approval_id.strip():
            raise ValueError(
                "approval_id must not be empty"
            )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )