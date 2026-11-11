from dataclasses import dataclass
from uuid import UUID

from .base import DomainEvent


@dataclass(frozen=True)
class FillCreatedEvent(DomainEvent):
    """
    Event emitted when an execution fill
    is created.

    Represents an actual executed
    market transaction component.

    Supports:

    - Execution audit
    - Position updates
    - Portfolio calculations
    - Event replay
    - Future risk analytics
    """


    fill_id: UUID = None

    execution_id: UUID = None

    quantity: str = ""

    price: str = ""

    venue: str | None = None


    def __post_init__(self):

        if self.fill_id is None:
            raise ValueError(
                "fill_id is required"
            )


        if self.execution_id is None:
            raise ValueError(
                "execution_id is required"
            )