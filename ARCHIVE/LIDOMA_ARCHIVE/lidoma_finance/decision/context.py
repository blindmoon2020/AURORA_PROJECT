from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class FinancialDecisionContext:

    context_id: str

    symbol: str

    market_state: dict[str, Any] = field(
        default_factory=dict
    )

    portfolio_state: dict[str, Any] = field(
        default_factory=dict
    )

    risk_state: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.context_id.strip():
            raise ValueError(
                "context_id must not be empty"
            )

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )