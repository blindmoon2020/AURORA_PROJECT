from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DataProvenance:
    """
    Tracks origin and lifecycle of every data object.
    """

    data_id: str

    source_id: str

    extraction_method: str

    collected_at: datetime

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

        if not self.extraction_method.strip():
            raise ValueError(
                "extraction_method must not be empty"
            )

        if not self.version.strip():
            raise ValueError(
                "version must not be empty"
            )

        if (
            self.collected_at.tzinfo is None
            or self.collected_at.utcoffset() is None
        ):
            raise ValueError(
                "collected_at must be timezone-aware"
            )