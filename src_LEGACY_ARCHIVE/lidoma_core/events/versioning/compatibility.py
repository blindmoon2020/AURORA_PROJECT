from .event_schema import (
    EventSchema,
)


class EventCompatibilityChecker:


    def compatible(
        self,
        source: EventSchema,
        target: EventSchema,
    ) -> bool:

        return (
            source.event_type ==
            target.event_type
            and
            source.version <=
            target.version
        )