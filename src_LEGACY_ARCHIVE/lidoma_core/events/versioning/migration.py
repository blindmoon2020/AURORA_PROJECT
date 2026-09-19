from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EventMigration:

    event_type: str

    from_version: int

    to_version: int


    def migrate(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        if self.from_version == self.to_version:
            return payload.copy()

        return payload.copy()