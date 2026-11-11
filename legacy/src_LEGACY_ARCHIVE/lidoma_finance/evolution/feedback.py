from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class EvolutionFeedback:

    feedback_id: str

    experience_id: str

    improvement_signal: str

    metrics: dict[str, Any]

    created_at: datetime


    def __post_init__(self):

        if not self.feedback_id.strip():
            raise ValueError(
                "feedback_id must not be empty"
            )

        if not self.experience_id.strip():
            raise ValueError(
                "experience_id must not be empty"
            )

        if not self.improvement_signal.strip():
            raise ValueError(
                "improvement_signal must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )