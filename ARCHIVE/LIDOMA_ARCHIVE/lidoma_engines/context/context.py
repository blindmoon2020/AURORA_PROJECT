from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DecisionContext:

    decision_id: str | None = None

    request_id: str | None = None

    market: str = ""

    timeframe: str = ""

    asset_class: str = ""

    instrument: str = ""

    signals: tuple[str, ...] = ()

    market_context: dict[str, Any] = field(
        default_factory=dict
    )

    risk_context: dict[str, Any] = field(
        default_factory=dict
    )

    portfolio_context: dict[str, Any] = field(
        default_factory=dict
    )

    user_context: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if self.decision_id is not None:

            if not self.decision_id.strip():
                raise ValueError(
                    "decision_id must not be empty"
                )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        if not self.request_id:

            object.__setattr__(
                self,
                "request_id",
                self.decision_id or "context-request"
            )

        if self.decision_id is None:

            object.__setattr__(
                self,
                "decision_id",
                self.request_id
            )