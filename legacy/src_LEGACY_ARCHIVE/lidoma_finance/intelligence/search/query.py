from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SearchQuery:
    """
    Standard intelligence search request.
    """


    query_id: str

    text: str

    requester: str

    created_at: datetime

    max_results: int = 10


    def __post_init__(self):

        if not self.query_id.strip():
            raise ValueError(
                "query_id required"
            )


        if not self.text.strip():
            raise ValueError(
                "query text required"
            )


        if not self.requester.strip():
            raise ValueError(
                "requester required"
            )


        if self.max_results <= 0:
            raise ValueError(
                "max_results must be positive"
            )


        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )