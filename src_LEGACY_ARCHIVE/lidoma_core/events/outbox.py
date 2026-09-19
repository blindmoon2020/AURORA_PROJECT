from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4



class OutboxStatus(str, Enum):
    """
    Lifecycle state of an outbox message.
    """

    PENDING = "PENDING"

    PROCESSING = "PROCESSING"

    PUBLISHED = "PUBLISHED"

    FAILED = "FAILED"




@dataclass
class OutboxMessage:
    """
    Persistent representation of a domain event.

    The outbox message guarantees that
    domain changes and event delivery
    can be handled separately.
    """


    event_id: UUID

    event_type: str

    payload: dict[str, Any]


    status: OutboxStatus = (
        OutboxStatus.PENDING
    )


    message_id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    published_at: datetime | None = None


    retry_count: int = 0



    def mark_processing(self) -> None:
        """
        Mark message as being processed.
        """

        if self.status != OutboxStatus.PENDING:

            raise ValueError(
                "Only pending messages can be processed"
            )


        self.status = (
            OutboxStatus.PROCESSING
        )



    def mark_published(self) -> None:
        """
        Mark message as successfully published.
        """

        if self.status not in (
            OutboxStatus.PROCESSING,
            OutboxStatus.PENDING,
        ):

            raise ValueError(
                "Message cannot be published"
            )


        self.status = (
            OutboxStatus.PUBLISHED
        )


        self.published_at = (
            datetime.now(timezone.utc)
        )



    def mark_failed(self) -> None:
        """
        Mark message delivery as failed.
        """

        self.status = (
            OutboxStatus.FAILED
        )

        self.retry_count += 1





class OutboxStore:
    """
    In-memory outbox storage.

    Future implementations:

    - PostgreSQL
    - Redis
    - Message queues
    """


    def __init__(self):

        self._messages: list[
            OutboxMessage
        ] = []



    def add(
        self,
        message: OutboxMessage,
    ) -> None:
        """
        Store new outbox message.
        """

        self._messages.append(
            message
        )



    def pending_messages(
        self,
    ) -> list[OutboxMessage]:
        """
        Return messages waiting for publishing.
        """

        return [

            message

            for message in self._messages

            if message.status
            == OutboxStatus.PENDING

        ]



    def mark_published(
        self,
        message: OutboxMessage,
    ) -> None:
        """
        Publish helper.
        """

        message.mark_published()



    def mark_failed(
        self,
        message: OutboxMessage,
    ) -> None:
        """
        Failure helper.
        """

        message.mark_failed()