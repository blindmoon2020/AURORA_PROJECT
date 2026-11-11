from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..enums import ExecutionStatus

from ..value_objects import (
    Price,
    Quantity,
)


@dataclass
class Execution:
    """
    Core execution entity.

    Represents the actual
    execution result of an order.

    Supports:

    - Crypto
    - Forex
    - Stocks
    - Futures
    - Exchange integrations
    """

    order_id: UUID

    quantity: Quantity

    price: Price

    status: ExecutionStatus = ExecutionStatus.CREATED

    venue: str | None = None

    exchange_execution_id: str | None = None


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    metadata: dict[str, object] = field(
        default_factory=dict
    )


    def submit(self) -> None:
        """
        Submit execution request.
        """

        if self.status != ExecutionStatus.CREATED:
            raise ValueError(
                "Only created executions can be submitted"
            )

        self.status = ExecutionStatus.SUBMITTED


    def complete(self) -> None:
        """
        Mark execution as completed.
        """

        if self.status not in (
            ExecutionStatus.SUBMITTED,
            ExecutionStatus.PARTIAL,
        ):
            raise ValueError(
                "Execution cannot be completed"
            )

        self.status = ExecutionStatus.COMPLETED


    def fail(self) -> None:
        """
        Mark execution as failed.
        """

        if self.status == ExecutionStatus.COMPLETED:
            raise ValueError(
                "Completed execution cannot fail"
            )

        self.status = ExecutionStatus.FAILED