from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RiskExplanation:

    risk_type: str

    score: float

    factors: dict[str, Any] = field(
        default_factory=dict
    )


    def __post_init__(self):

        if not self.risk_type.strip():
            raise ValueError(
                "risk_type must not be empty"
            )

        if self.score < 0.0:
            raise ValueError(
                "score must be >= 0"
            )

        if self.score > 1.0:
            raise ValueError(
                "score must be <= 1"
            )