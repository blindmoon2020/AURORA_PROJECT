from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CanonicalDataObject:
    """
    Standard LIDOMA normalized data object.
    """


    data_id: str

    source_id: str

    data_type: str

    payload: Any

    timestamp: datetime

    version: str


    def __post_init__(self):

        if not self.data_id.strip():
            raise ValueError(
                "data_id must not be empty"
            )


        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )


        if not self.data_type.strip():
            raise ValueError(
                "data_type must not be empty"
            )


        if not self.version.strip():
            raise ValueError(
                "version must not be empty"
            )


        if (
            self.timestamp.tzinfo is None
            or self.timestamp.utcoffset() is None
        ):
            raise ValueError(
                "timestamp must be timezone-aware"
            )