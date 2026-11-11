from lidoma_engines.risk.assessment import (
    RiskAssessment,
)


class RiskEngine:

    def assess(
        self,
        portfolio_id: str,
        metrics: dict,
    ) -> RiskAssessment:

        if not portfolio_id.strip():
            raise ValueError(
                "portfolio_id must not be empty"
            )

        risk_score = self._calculate_score(
            metrics
        )

        return RiskAssessment(
            assessment_id=f"risk.{portfolio_id}",
            portfolio_id=portfolio_id,
            risk_score=risk_score,
            metrics=metrics,
        )


    def _calculate_score(
        self,
        metrics: dict,
    ) -> float:

        if not metrics:
            return 0.0

        values = [
            float(value)
            for value in metrics.values()
        ]

        score = sum(values) / len(values)

        return round(
            score,
            2,
        )