from lidoma_engines.decision.calibration import (
    ConfidenceCalibrationEngine,
)


def test_high_accuracy_increases_confidence():

    result = ConfidenceCalibrationEngine().calibrate(
        0.7,
        0.9,
    )

    assert result.calibrated_confidence > 0.7
    assert result.adjustment == 0.4


def test_low_accuracy_decreases_confidence():

    result = ConfidenceCalibrationEngine().calibrate(
        0.7,
        0.1,
    )

    assert result.calibrated_confidence < 0.7
    assert result.adjustment == -0.4


def test_confidence_is_clamped():

    result = ConfidenceCalibrationEngine().calibrate(
        0.95,
        1.0,
    )

    assert result.calibrated_confidence <= 1.0