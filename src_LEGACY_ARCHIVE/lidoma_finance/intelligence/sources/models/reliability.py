from dataclasses import dataclass


@dataclass(frozen=True)
class SourceReliability:

    source_id: str

    trust_score: float

    validation_count: int

    approved: bool


    def __post_init__(self):

        if not self.source_id.strip():
            raise ValueError(
                "source_id must not be empty"
            )

        if not 0 <= self.trust_score <= 1:
            raise ValueError(
                "trust_score must be between 0 and 1"
            )

        if self.validation_count < 0:
            raise ValueError(
                "validation_count cannot be negative"
            )