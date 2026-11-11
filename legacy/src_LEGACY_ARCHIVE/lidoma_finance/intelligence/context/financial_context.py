from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class FinancialAIContext:
    """
    Standard context package for AI reasoning.
    """


    context_id: str

    market_data: Any

    knowledge: Any

    analysis: Any

    sources: list[str]

    confidence_score: float

    created_at: datetime

    version: str


    def __post_init__(self):

        if not self.context_id.strip():
            raise ValueError(
                "context_id required"
            )


        if not self.version.strip():
            raise ValueError(
                "version required"
            )


        if not 0 <= self.confidence_score <= 1:
            raise ValueError(
                "confidence_score must be between 0 and 1"
            )


        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )