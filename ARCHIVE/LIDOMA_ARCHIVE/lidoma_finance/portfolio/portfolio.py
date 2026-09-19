from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Portfolio:

    portfolio_id: str

    name: str

    assets: dict[str, float] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.portfolio_id.strip():
            raise ValueError(
                "portfolio_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "portfolio name must not be empty"
            )

        for symbol, allocation in self.assets.items():

            if not symbol.strip():
                raise ValueError(
                    "asset symbol must not be empty"
                )

            if allocation < 0:
                raise ValueError(
                    "allocation cannot be negative"
                )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )