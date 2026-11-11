from dataclasses import dataclass


@dataclass(frozen=True)
class ExposureRiskAssessment:

    gross_exposure: float

    net_exposure: float


    @property
    def risk_score(self) -> float:

        score = (
            abs(self.gross_exposure)
            +
            abs(self.net_exposure)
        ) / 2

        return round(
            min(
                max(score, 0.0),
                1.0,
            ),
            10,
        )