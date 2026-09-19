from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptiveReliabilityScore:
    source_id: str
    historical_accuracy: float
    calibration_factor: float
    freshness_factor: float
    governance_factor: float
    final_score: float
    reason: str

    def __post_init__(self) -> None:

        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )

        values = (
            self.historical_accuracy,
            self.calibration_factor,
            self.freshness_factor,
            self.governance_factor,
            self.final_score,
        )

        for value in values:
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    "scores must be between 0 and 1"
                )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


class AdaptiveReliabilityScorer:
    """
    Calculates adaptive reliability score.

    Does not:
    - mutate reliability
    - change source profiles
    - execute decisions
    """

    def calculate(
        self,
        *,
        source_id: str,
        historical_accuracy: float,
        calibration_factor: float,
        freshness_factor: float,
        governance_factor: float,
    ) -> AdaptiveReliabilityScore:

        final_score = (
            historical_accuracy * 0.4
            +
            calibration_factor * 0.2
            +
            freshness_factor * 0.2
            +
            governance_factor * 0.2
        )

        return AdaptiveReliabilityScore(
            source_id=source_id,
            historical_accuracy=historical_accuracy,
            calibration_factor=calibration_factor,
            freshness_factor=freshness_factor,
            governance_factor=governance_factor,
            final_score=round(final_score, 4),
            reason="adaptive_weighted_reliability_score",
        )