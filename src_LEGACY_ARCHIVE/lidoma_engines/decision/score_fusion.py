from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveDecisionScore:
    consensus_score: float
    calibrated_confidence: float
    reliability_score: float
    freshness_factor: float
    governance_factor: float
    final_score: float
    reason: str

    def __post_init__(self) -> None:

        values = (
            self.consensus_score,
            self.calibrated_confidence,
            self.reliability_score,
            self.freshness_factor,
            self.governance_factor,
            self.final_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "score values must be between 0 and 1"
                )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


class AdaptiveDecisionScoreFusion:

    def calculate(
        self,
        *,
        consensus_score: float,
        calibrated_confidence: float,
        reliability_score: float,
        freshness_factor: float,
        governance_factor: float,
    ) -> AdaptiveDecisionScore:

        final_score = (
            consensus_score * 0.30
            +
            calibrated_confidence * 0.25
            +
            reliability_score * 0.20
            +
            freshness_factor * 0.15
            +
            governance_factor * 0.10
        )

        return AdaptiveDecisionScore(
            consensus_score=consensus_score,
            calibrated_confidence=calibrated_confidence,
            reliability_score=reliability_score,
            freshness_factor=freshness_factor,
            governance_factor=governance_factor,
            final_score=round(final_score, 4),
            reason="adaptive_decision_score_fusion",
        )