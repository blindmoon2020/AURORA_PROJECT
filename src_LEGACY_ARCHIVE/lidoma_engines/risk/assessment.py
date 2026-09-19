from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RiskAssessment:

    assessment_id: str

    portfolio_id: str

    risk_score: float

    metrics: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.assessment_id.strip():
            raise ValueError(
                "assessment_id must not be empty"
            )

        if not self.portfolio_id.strip():
            raise ValueError(
                "portfolio_id must not be empty"
            )

        if not 0 <= self.risk_score <= 1:
            raise ValueError(
                "risk_score must be between 0 and 1"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )