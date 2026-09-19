from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all LIDOMA domain events.

    Domain events represent facts that
    already happened inside the domain.

    Design goals:

    - Immutable event history
    - Audit capability
    - Replay readiness
    - Idempotency preparation
    - Distributed tracing support


    Future compatible with:

    - Event Sourcing
    - Outbox Pattern
    - Message Brokers
    - AI Decision Traceability
    """


    event_id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    occurred_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    version: int = field(
        default=1,
        init=False,
    )


    source: str = field(
        default="lidoma_core",
        init=False,
    )


    correlation_id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    causation_id: UUID | None = field(
        default=None,
        init=False,
    )


    metadata: dict[str, Any] = field(
        default_factory=dict,
        init=False,
    )


    @property
    def event_type(self) -> str:
        """
        Returns unique event type name.

        Used for:

        - routing
        - persistence
        - replay
        """

        return self.__class__.__name__


    def with_causation(
        self,
        causation_id: UUID,
    ) -> "DomainEvent":
        """
        Create a logically related event chain.

        Example:

        OrderCreatedEvent
                |
                |
                v
        ExecutionSubmittedEvent

        The second event can reference
        the first event as causation.
        """


        object.__setattr__(
            self,
            "causation_id",
            causation_id,
        )

        return self


    def add_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:
        """
        Attach additional event information.

        Examples:

        {
            "strategy": "momentum",
            "agent": "risk_engine",
            "environment": "production"
        }
        """


        self.metadata[key] = value