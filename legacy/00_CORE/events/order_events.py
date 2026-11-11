from dataclasses import dataclass
from uuid import UUID

from .base import DomainEvent

from ..models.entities import Order


@dataclass(frozen=True)
class OrderCreatedEvent(DomainEvent):
    """
    Event emitted when a new order
    is created inside AURORA domain.

    Used for:

    - Audit
    - Order workflow
    - Event replay
    - Analytics
    """


    order_id: UUID = None

    symbol: str = ""

    side: str = ""

    order_type: str = ""

    quantity: str = ""


    def __post_init__(self):

        if self.order_id is None:
            raise ValueError(
                "order_id is required"
            )
