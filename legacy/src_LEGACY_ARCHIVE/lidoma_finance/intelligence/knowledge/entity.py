from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class KnowledgeEntity:
    """
    Unified knowledge object for LIDOMA.
    """


    entity_id: str

    entity_type: str

    source_id: str

    content: Any

    created_at: datetime

    version: str


    def __post_init__(self):

        if not self.entity_id.strip():
            raise ValueError(
                "entity_id required"
            )


        if not self.entity_type.strip():
            raise ValueError(
                "entity_type required"
            )


        if not self.source_id.strip():
            raise ValueError(
                "source_id required"
            )


        if not self.version.strip():
            raise ValueError(
                "version required"
            )


        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )