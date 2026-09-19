from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDecisionResult:
    decision_id: str
    adaptive_score: float
    quality_score: float
    final_score: float
    approved: bool
    reason: str

    def __post_init__(self) -> None:

        values = (
            self.adaptive_score,
            self.quality_score,
            self.final_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "scores must be between 0 and 1"
                )

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


class DecisionRuntimeIntegration:
    """
    Final Phase 6 runtime integration.

    Combines:
    - adaptive decision score
    - historical quality score

    Does not:
    - execute external actions
    - bypass governance
    - mutate memory
    """

    def evaluate(
        self,
        *,
        decision_id: str,
        adaptive_score: float,
        quality_score: float,
    ) -> RuntimeDecisionResult:

        final_score = (
            adaptive_score * 0.6
            +
            quality_score * 0.4
        )

        approved = final_score >= 0.7

        return RuntimeDecisionResult(
            decision_id=decision_id,
            adaptive_score=adaptive_score,
            quality_score=quality_score,
            final_score=round(final_score, 4),
            approved=approved,
            reason="phase_6_runtime_integration",
        )