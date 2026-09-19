from dataclasses import asdict, fields
from typing import Any

from ..events import DomainEvent

from ..events.outbox import (
    OutboxMessage,
)



class EventOutboxMapper:
    """
    Converts domain events into
    persistent outbox messages.

    Responsibilities:

    - Serialize domain events
    - Preserve event identity
    - Preserve tracing information
    - Prepare reliable delivery


    Supports:

    - Order Events
    - Execution Events
    - Fill Events
    - Portfolio Events
    - Future Risk Events
    """


    def map(
        self,
        event: DomainEvent,
    ) -> OutboxMessage:
        """
        Convert DomainEvent into OutboxMessage.
        """


        if not isinstance(
            event,
            DomainEvent,
        ):
            raise TypeError(
                "Only DomainEvent instances can be mapped"
            )


        payload = self._serialize(
            event
        )


        return OutboxMessage(

            event_id=event.event_id,

            event_type=event.event_type,

            payload=payload,

        )



    def _serialize(
        self,
        event: DomainEvent,
    ) -> dict[str, Any]:
        """
        Serialize event data.

        Keeps domain event independent
        from storage implementation.
        """


        result: dict[str, Any] = {}


        for item in fields(event):

            value = getattr(
                event,
                item.name,
            )


            if hasattr(
                value,
                "hex",
            ):

                value = str(value)


            elif hasattr(
                value,
                "isoformat",
            ):

                value = value.isoformat()


            result[item.name] = value


        result["event_type"] = (
            event.event_type
        )


        return result