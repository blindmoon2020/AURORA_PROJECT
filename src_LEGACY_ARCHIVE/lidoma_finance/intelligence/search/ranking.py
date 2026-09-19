from dataclasses import dataclass


@dataclass(frozen=True)
class SearchRanking:

    entity_id: str

    relevance_score: float

    source_trust_score: float

    final_score: float


    def __post_init__(self):

        if not self.entity_id.strip():
            raise ValueError(
                "entity_id required"
            )


        for value in (
            self.relevance_score,
            self.source_trust_score,
            self.final_score,
        ):

            if not 0 <= value <= 1:
                raise ValueError(
                    "scores must be between 0 and 1"
                )