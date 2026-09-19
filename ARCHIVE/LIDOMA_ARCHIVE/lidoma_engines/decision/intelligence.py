from dataclasses import dataclass

from .evaluation import DecisionPerformance
from .memory import DecisionMemoryRecord


@dataclass(frozen=True)
class ReliabilityAdjustmentProposal:
    """
    Suggests reliability adjustment based on historical outcomes.

    This object is advisory only.

    It does NOT:
    - mutate reliability
    - modify source weights
    - execute decisions
    """

    source_id: str
    evaluated_decisions: int
    success_rate: float
    proposed_adjustment: float
    reason: str

    def __post_init__(self) -> None:

        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )

        if self.evaluated_decisions < 0:
            raise ValueError(
                "evaluated_decisions must not be negative"
            )

        if not 0.0 <= self.success_rate <= 1.0:
            raise ValueError(
                "success_rate must be between 0 and 1"
            )

        if not -1.0 <= self.proposed_adjustment <= 1.0:
            raise ValueError(
                "proposed_adjustment must be between -1 and 1"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


class DecisionIntelligenceEngine:
    """
    Converts historical decision performance
    into reliability adjustment proposals.

    No automatic learning.
    No automatic mutation.
    """

    def build_source_proposal(
        self,
        source_id: str,
        records: tuple[
            DecisionMemoryRecord,
            ...,
        ],
    ) -> ReliabilityAdjustmentProposal:

        successful = 0
        failed = 0

        for record in records:

            if record.decision.evidence_ids:

                if record.outcome is None:
                    continue

                from .outcome import (
                    DecisionOutcomeStatus,
                )

                if (
                    record.outcome.status
                    == DecisionOutcomeStatus.SUCCESS
                ):
                    successful += 1

                elif (
                    record.outcome.status
                    == DecisionOutcomeStatus.FAILURE
                ):
                    failed += 1

        total = successful + failed

        if total == 0:
            return ReliabilityAdjustmentProposal(
                source_id=source_id,
                evaluated_decisions=0,
                success_rate=0.0,
                proposed_adjustment=0.0,
                reason=(
                    "insufficient_historical_outcomes"
                ),
            )

        success_rate = successful / total

        adjustment = (
            success_rate - 0.5
        )

        return ReliabilityAdjustmentProposal(
            source_id=source_id,
            evaluated_decisions=total,
            success_rate=success_rate,
            proposed_adjustment=adjustment,
            reason=(
                "historical_performance_based_proposal"
            ),
        )