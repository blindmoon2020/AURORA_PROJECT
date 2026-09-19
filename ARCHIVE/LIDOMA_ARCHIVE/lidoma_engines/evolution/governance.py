from dataclasses import dataclass
from enum import Enum

from lidoma_engines.adaptation import DecisionAdaptation


class EvolutionGovernanceDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvolutionGovernanceReview:
    adaptation: DecisionAdaptation
    decision: EvolutionGovernanceDecision
    reviewer: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, EvolutionGovernanceDecision):
            raise TypeError(
                "decision must be an EvolutionGovernanceDecision"
            )

        if not isinstance(self.reviewer, str):
            raise TypeError("reviewer must be a string")

        if not self.reviewer.strip():
            raise ValueError("reviewer must not be empty")

        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")

        if not self.reason.strip():
            raise ValueError("reason must not be empty")

    @property
    def is_approved(self) -> bool:
        return self.decision == EvolutionGovernanceDecision.APPROVED


class EvolutionGovernanceGate:
    """
    Explicit governance gate for adaptation proposals.

    This gate:
    - never applies an adaptation
    - never mutates strategy state
    - never mutates runtime state
    - only records approval or rejection
    """

    def review(
        self,
        *,
        adaptation: DecisionAdaptation,
        decision: EvolutionGovernanceDecision,
        reviewer: str,
        reason: str,
    ) -> EvolutionGovernanceReview:
        return EvolutionGovernanceReview(
            adaptation=adaptation,
            decision=decision,
            reviewer=reviewer.strip(),
            reason=reason.strip(),
        )