from dataclasses import dataclass

from .memory import DecisionMemoryRecord
from .outcome import DecisionOutcomeStatus


@dataclass(frozen=True)
class DecisionPerformance:
    """
    Historical performance statistics for evaluated decisions.
    """

    total_evaluated: int
    successful: int
    failed: int

    def __post_init__(self) -> None:
        if self.total_evaluated < 0:
            raise ValueError("total_evaluated cannot be negative")

        if self.successful < 0:
            raise ValueError("successful cannot be negative")

        if self.failed < 0:
            raise ValueError("failed cannot be negative")

        if self.successful + self.failed != self.total_evaluated:
            raise ValueError("invalid performance counters")

    @property
    def accuracy(self) -> float:
        if self.total_evaluated == 0:
            return 0.0

        return self.successful / self.total_evaluated


class DecisionEvaluator:
    """
    Calculates historical decision performance.

    UNKNOWN and unevaluated outcomes are excluded from
    success/failure accuracy calculations.
    """

    def evaluate(
        self,
        records: tuple[DecisionMemoryRecord, ...],
    ) -> DecisionPerformance:
        successful = 0
        failed = 0

        for record in records:
            if record.outcome is None:
                continue

            if record.outcome.status == DecisionOutcomeStatus.SUCCESS:
                successful += 1

            elif record.outcome.status == DecisionOutcomeStatus.FAILURE:
                failed += 1

        return DecisionPerformance(
            total_evaluated=successful + failed,
            successful=successful,
            failed=failed,
        )