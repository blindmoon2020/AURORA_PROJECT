from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..value_objects import (
    Price,
    Quantity,
)


@dataclass
class Fill:
    """
    Core fill entity.

    Represents an individual
    executed trade component.

    A single execution may contain
    multiple fills.

    Supports multi-asset trading
    across exchanges and brokers.
    """

    execution_id: UUID

    quantity: Quantity

    price: Price


    venue: str | None = None

    exchange_fill_id: str | None = None


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    executed_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    metadata: dict[str, object] = field(
        default_factory=dict
    )