from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceCalibration:
    """
    Calibrated confidence result.
    """

    original_confidence: float
    calibrated_confidence: float
    adjustment: float
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.original_confidence <= 1.0:
            raise ValueError(
                "original_confidence must be between 0 and 1"
            )

        if not 0.0 <= self.calibrated_confidence <= 1.0:
            raise ValueError(
                "calibrated_confidence must be between 0 and 1"
            )

        if not -1.0 <= self.adjustment <= 1.0:
            raise ValueError(
                "adjustment must be between -1 and 1"
            )

        if not self.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )


class ConfidenceCalibrationEngine:
    """
    Adjusts confidence using historical performance.

    Does not modify decisions.
    Does not mutate reliability.
    """

    def calibrate(
        self,
        confidence: float,
        historical_accuracy: float,
    ) -> ConfidenceCalibration:

        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if not 0.0 <= historical_accuracy <= 1.0:
            raise ValueError(
                "historical_accuracy must be between 0 and 1"
            )

        adjustment = (
            historical_accuracy - 0.5
        )

        calibrated = confidence + (
            adjustment * 0.2
        )

        calibrated = max(
            0.0,
            min(
                1.0,
                calibrated,
            ),
        )

        return ConfidenceCalibration(
            original_confidence=confidence,
            calibrated_confidence=calibrated,
            adjustment=adjustment,
            reason=(
                "historical_accuracy_calibration"
            ),
        )