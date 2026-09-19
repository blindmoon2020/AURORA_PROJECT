from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class StrategyDefinition:

    strategy_id: str

    name: str

    description: str

    parameters: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.strategy_id.strip():
            raise ValueError(
                "strategy_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "strategy name must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )