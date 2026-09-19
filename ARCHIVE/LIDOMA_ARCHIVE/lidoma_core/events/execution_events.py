from dataclasses import dataclass
from uuid import UUID

from .base import DomainEvent


@dataclass(frozen=True)
class ExecutionSubmittedEvent(DomainEvent):
    """
    Event emitted when an execution
    request is submitted.

    Supports:

    - Execution workflow tracking
    - Audit trail
    - Replay
    - Execution analytics
    """


    execution_id: UUID = None

    order_id: UUID = None

    quantity: str = ""

    price: str = ""

    venue: str | None = None


    def __post_init__(self):

        if self.execution_id is None:
            raise ValueError(
                "execution_id is required"
            )

        if self.order_id is None:
            raise ValueError(
                "order_id is required"
            )