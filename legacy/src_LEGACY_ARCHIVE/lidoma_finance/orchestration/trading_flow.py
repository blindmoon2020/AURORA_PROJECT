from dataclasses import dataclass

from ..decision import (
    FinancialDecisionEngine,
    FinancialDecisionContext,
)

from ..risk import (
    RiskGate,
    FinancialRiskAssessment,
)

from ..execution import (
    ExecutionApproval,
)


@dataclass
class TradingWorkflow:


    decision_engine: FinancialDecisionEngine

    risk_gate: RiskGate


    def evaluate(
        self,
        context: FinancialDecisionContext,
        risk: FinancialRiskAssessment,
    ):

        decision = self.decision_engine.evaluate(
            context
        )

        approved = self.risk_gate.approve(
            risk
        )

        approval = ExecutionApproval(
            approval_id=f"APP-{decision.decision_id}",
            decision_id=decision.decision_id,
            approved=approved,
            reason=(
                "Risk approved"
                if approved
                else
                "Risk rejected"
            ),
            created_at=decision.created_at,
        )

        return approval