from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionQualityScore:
    decision_id: str
    accuracy_score: float
    confidence_score: float
    reliability_score: float
    outcome_score: float
    final_score: float
    reason: str

    def __post_init__(self) -> None:
        values = (
            self.accuracy_score,
            self.confidence_score,
            self.reliability_score,
            self.outcome_score,
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


class DecisionQualityRanker:
    """
    Calculates historical decision quality.

    Does not:
    - mutate decisions
    - change reliability
    - bypass governance
    """

    def calculate(
        self,
        *,
        decision_id: str,
        accuracy_score: float,
        confidence_score: float,
        reliability_score: float,
        outcome_score: float,
    ) -> DecisionQualityScore:

        final_score = (
            accuracy_score * 0.35
            +
            confidence_score * 0.25
            +
            reliability_score * 0.20
            +
            outcome_score * 0.20
        )

        return DecisionQualityScore(
            decision_id=decision_id,
            accuracy_score=accuracy_score,
            confidence_score=confidence_score,
            reliability_score=reliability_score,
            outcome_score=outcome_score,
            final_score=round(final_score, 4),
            reason="decision_quality_ranking",
        )