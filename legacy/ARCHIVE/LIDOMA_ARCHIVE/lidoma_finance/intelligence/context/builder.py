from dataclasses import dataclass
from datetime import datetime, timezone

from .financial_context import FinancialAIContext


@dataclass
class FinancialContextBuilder:
    """
    Creates AI-ready financial contexts.
    """


    version: str = "1.0"


    def build(
        self,
        context_id: str,
        market_data,
        knowledge,
        analysis,
        sources,
        confidence_score: float,
    ) -> FinancialAIContext:


        return FinancialAIContext(

            context_id=context_id,

            market_data=market_data,

            knowledge=knowledge,

            analysis=analysis,

            sources=sources,

            confidence_score=confidence_score,

            created_at=datetime.now(
                timezone.utc
            ),

            version=self.version,

        )