from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DecisionOutcomeStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class DecisionOutcome:
    """
    Immutable realized outcome of a decision.

    Records what happened after a decision without
    executing orders, mutating portfolios, or changing
    source reliability.
    """

    decision_id: str
    status: DecisionOutcomeStatus
    evaluated_at: datetime
    realized_return: float | None = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("decision_id must not be empty")

        if not isinstance(self.status, DecisionOutcomeStatus):
            raise TypeError("status must be DecisionOutcomeStatus")

        if (
            self.evaluated_at.tzinfo is None
            or self.evaluated_at.utcoffset() is None
        ):
            raise ValueError("evaluated_at must be timezone-aware")

        if self.realized_return is not None:
            if isinstance(self.realized_return, bool) or not isinstance(
                self.realized_return,
                (int, float),
            ):
                raise TypeError("realized_return must be numeric")