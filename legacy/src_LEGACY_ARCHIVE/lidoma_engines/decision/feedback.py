from dataclasses import dataclass
from enum import Enum

from .intelligence import ReliabilityAdjustmentProposal


class FeedbackDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class FeedbackReview:
    proposal: ReliabilityAdjustmentProposal
    decision: FeedbackDecision
    reviewer: str
    reason: str

    def __post_init__(self) -> None:

        if not self.reviewer.strip():
            raise ValueError(
                "reviewer must not be empty"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


@dataclass(frozen=True)
class ReliabilityFeedbackRecord:
    source_id: str
    adjustment: float
    approved: bool
    reason: str

    def __post_init__(self) -> None:

        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )

        if not -1.0 <= self.adjustment <= 1.0:
            raise ValueError(
                "adjustment must be between -1 and 1"
            )


class FeedbackGovernanceEngine:
    """
    Controls feedback approval.

    Never mutates reliability directly.
    """

    def review(
        self,
        review: FeedbackReview,
    ) -> ReliabilityFeedbackRecord:

        approved = (
            review.decision
            ==
            FeedbackDecision.APPROVED
        )

        adjustment = 0.0

        if approved:
            adjustment = (
                review.proposal.proposed_adjustment
            )

        return ReliabilityFeedbackRecord(
            source_id=(
                review.proposal.source_id
            ),
            adjustment=adjustment,
            approved=approved,
            reason=review.reason,
        )