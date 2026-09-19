from dataclasses import dataclass

from .context import FinancialDecisionContext
from .decision import FinancialDecision


@dataclass(frozen=True)
class FinancialDecisionEngine:


    def evaluate(
        self,
        context: FinancialDecisionContext,
    ) -> FinancialDecision:

        confidence = 0.0
        action = "HOLD"


        if context.market_state:

            confidence = 0.5
            action = "HOLD"


        return FinancialDecision(
            decision_id=f"DEC-{context.context_id}",
            symbol=context.symbol,
            action=action,
            confidence=confidence,
            created_at=context.created_at,
        )