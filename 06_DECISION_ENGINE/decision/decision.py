from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class DecisionAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True)
class Decision:
    action: DecisionAction
    confidence: float
    reasoning: tuple[str, ...]
    created_at: datetime
    decision_id: str = field(default_factory=lambda: str(uuid4()))
    evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    conflict_ratio: float = 0.0
    consensus_score: float = 0.0
    independent_cluster_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.action, DecisionAction):
            raise TypeError("action must be a DecisionAction")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not self.reasoning:
            raise ValueError("decision requires reasoning")

        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")

        if not self.decision_id.strip():
            raise ValueError("decision_id must not be empty")

        if not 0.0 <= self.conflict_ratio <= 1.0:
            raise ValueError("conflict_ratio must be between 0 and 1")

        if not 0.0 <= self.consensus_score <= 1.0:
            raise ValueError("consensus_score must be between 0 and 1")

        if self.independent_cluster_count < 0:
            raise ValueError(
                "independent_cluster_count must not be negative"
            )

    @staticmethod
    def create(
        action: DecisionAction,
        confidence: float,
        reasoning: tuple[str, ...],
        *,
        evidence_ids: tuple[str, ...] = (),
        conflict_ratio: float = 0.0,
        consensus_score: float = 0.0,
        independent_cluster_count: int = 0,
    ) -> "Decision":
        return Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            created_at=datetime.now(timezone.utc),
            evidence_ids=evidence_ids,
            conflict_ratio=conflict_ratio,
            consensus_score=consensus_score,
            independent_cluster_count=independent_cluster_count,
        )
