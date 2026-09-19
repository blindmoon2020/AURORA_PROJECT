from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DecisionExperience:

    experience_id: str

    decision_id: str

    outcome: str

    lessons: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.experience_id.strip():
            raise ValueError(
                "experience_id must not be empty"
            )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not self.outcome.strip():
            raise ValueError(
                "outcome must not be empty"
            )