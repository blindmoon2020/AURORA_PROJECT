from dataclasses import dataclass


@dataclass(frozen=True)
class MarketRiskAssessment:

    volatility: float

    price_change: float


    @property
    def risk_score(self) -> float:

        score = (
            abs(self.volatility)
            +
            abs(self.price_change)
        ) / 2

        return round(
            min(
                max(score, 0.0),
                1.0,
            ),
            10,
        )