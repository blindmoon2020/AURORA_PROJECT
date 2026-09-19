from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


DecisionAction = Literal[
    "BUY",
    "SELL",
    "HOLD",
]


@dataclass(frozen=True)
class FinancialDecision:

    decision_id: str

    symbol: str

    action: DecisionAction

    confidence: float

    created_at: datetime


    def __post_init__(self):

        if not self.decision_id.strip():
            raise ValueError(
                "decision_id must not be empty"
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if not 0 <= self.confidence <= 1:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )