from dataclasses import dataclass


@dataclass(frozen=True)
class PortfolioRiskAssessment:

    exposure: float

    concentration: float


    @property
    def risk_score(self) -> float:

        score = (
            abs(self.exposure)
            +
            abs(self.concentration)
        ) / 2

        return round(
            min(
                max(score, 0.0),
                1.0,
            ),
            10,
        )