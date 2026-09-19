from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EventSchema:

    event_type: str

    version: int

    fields: dict[str, Any] = field(
        default_factory=dict
    )


    def __post_init__(self):

        if not self.event_type.strip():
            raise ValueError(
                "event_type must not be empty"
            )

        if self.version < 1:
            raise ValueError(
                "version must be >= 1"
            )