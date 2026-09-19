from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RawDataPayload:
    """
    Raw extracted data container.
    """


    data_id: str

    source_id: str

    payload: Any

    collected_at: datetime


    def __post_init__(self):

        if not self.data_id.strip():
            raise ValueError(
                "data_id must not be empty"
            )


        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )


        if (
            self.collected_at.tzinfo is None
            or self.collected_at.utcoffset() is None
        ):
            raise ValueError(
                "collected_at must be timezone-aware"
            )