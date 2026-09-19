from dataclasses import dataclass

from .assessment import (
    FinancialRiskAssessment,
)


@dataclass(frozen=True)
class RiskGate:

    max_allowed_score: float = 0.7


    def approve(
        self,
        assessment: FinancialRiskAssessment,
    ) -> bool:

        return (
            assessment.risk_score
            <= self.max_allowed_score
            and assessment.approved
        )