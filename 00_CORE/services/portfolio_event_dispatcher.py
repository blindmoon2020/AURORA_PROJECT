from ..events import DomainEvent

from ..events.outbox import (
    OutboxMessage,
    OutboxStore,
)

from .event_outbox_mapper import (
    EventOutboxMapper,
)



class PortfolioEventDispatcher:
    """
    Dispatches portfolio domain events
    into the outbox reliability pipeline.

    Responsibilities:

    - Map domain events
    - Store outbox messages
    - Preserve reliable event flow

    Does NOT:

    - Change domain state
    - Publish messages
    - Handle retries
    """


    def __init__(
        self,
        outbox_store: OutboxStore | None = None,
        mapper: EventOutboxMapper | None = None,
    ):

        self.outbox_store = (
            outbox_store
            or OutboxStore()
        )


        self.mapper = (
            mapper
            or EventOutboxMapper()
        )



    def dispatch(
        self,
        event: DomainEvent,
    ) -> OutboxMessage:
        """
        Convert domain event into
        outbox message and persist it.
        """


        message = self.mapper.map(
            event
        )


        self.outbox_store.add(
            message
        )


        return message