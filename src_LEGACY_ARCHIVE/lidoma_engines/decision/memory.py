from dataclasses import dataclass
from datetime import datetime

from .decision import Decision
from .outcome import DecisionOutcome


@dataclass(frozen=True)
class DecisionMemoryRecord:
    """
    Immutable snapshot of a decision lifecycle.
    """

    decision: Decision
    created_at: datetime
    outcome: DecisionOutcome | None = None

    def __post_init__(self) -> None:
        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError("created_at must be timezone-aware")


class DecisionMemoryStore:
    """
    Storage contract for decision memory.
    """

    def save(self, record: DecisionMemoryRecord) -> None:
        raise NotImplementedError

    def get(self, decision_id: str) -> DecisionMemoryRecord | None:
        raise NotImplementedError

    def all(self) -> tuple[DecisionMemoryRecord, ...]:
        raise NotImplementedError


class InMemoryDecisionMemoryStore(DecisionMemoryStore):
    """
    Deterministic in-memory decision memory implementation.
    """

    def __init__(self) -> None:
        self._records: dict[str, DecisionMemoryRecord] = {}

    def save(self, record: DecisionMemoryRecord) -> None:
        self._records[record.decision.decision_id] = record

    def get(self, decision_id: str) -> DecisionMemoryRecord | None:
        return self._records.get(decision_id)

    def all(self) -> tuple[DecisionMemoryRecord, ...]:
        return tuple(self._records.values())