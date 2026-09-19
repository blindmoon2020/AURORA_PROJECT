from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SourceMetadata:
    """
    Identity and classification metadata
    for external intelligence sources.
    """

    source_id: str

    name: str

    source_type: str

    category: str

    access_method: str

    created_at: datetime

    enabled: bool = True


    def __post_init__(self):

        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "name must not be empty"
            )

        if not self.source_type.strip():
            raise ValueError(
                "source_type must not be empty"
            )

        if not self.category.strip():
            raise ValueError(
                "category must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )