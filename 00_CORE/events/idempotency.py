from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class EventFingerprint:
    """
    Unique identity of an event processing attempt.

    Used for:

    - duplicate detection
    - idempotent processing
    - replay safety
    """


    event_id: UUID

    event_type: str

    correlation_id: UUID



    def value(self) -> str:
        """
        Returns stable fingerprint string.
        """

        return (
            f"{self.event_type}:"
            f"{self.event_id}:"
            f"{self.correlation_id}"
        )



class IdempotencyRegistry:
    """
    In-memory idempotency storage.

    Future compatible with:

    - Redis
    - Database
    - Distributed event stores
    """


    def __init__(self):

        self._processed_events: set[str] = set()



    def is_processed(
        self,
        fingerprint: EventFingerprint,
    ) -> bool:
        """
        Check whether event was already processed.
        """

        return (
            fingerprint.value()
            in self._processed_events
        )



    def mark_processed(
        self,
        fingerprint: EventFingerprint,
    ) -> None:
        """
        Mark event as processed.
        """

        self._processed_events.add(
            fingerprint.value()
        )



    def clear(self) -> None:
        """
        Clear registry.

        Mainly useful for:

        - testing
        - development
        """

        self._processed_events.clear()