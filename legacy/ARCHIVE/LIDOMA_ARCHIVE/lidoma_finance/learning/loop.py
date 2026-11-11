from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class LearningCycle:

    cycle_id: str

    strategy_id: str

    experience_count: int

    improvement_score: float

    created_at: datetime


    def __post_init__(self):

        if not self.cycle_id.strip():
            raise ValueError(
                "cycle_id must not be empty"
            )

        if not self.strategy_id.strip():
            raise ValueError(
                "strategy_id must not be empty"
            )

        if self.experience_count < 0:
            raise ValueError(
                "experience_count cannot be negative"
            )

        if not 0 <= self.improvement_score <= 1:
            raise ValueError(
                "improvement_score must be between 0 and 1"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )