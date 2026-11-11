from dataclasses import dataclass


@dataclass(frozen=True)
class StressRiskAssessment:

    scenario: str

    impact: float


    @property
    def risk_score(self) -> float:

        score = abs(
            self.impact
        )

        return round(
            min(
                max(score, 0.0),
                1.0,
            ),
            10,
        )