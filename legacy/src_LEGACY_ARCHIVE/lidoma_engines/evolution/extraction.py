from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from lidoma_engines.experience import DecisionExperience
from lidoma_engines.patterns import DecisionPattern


@dataclass(frozen=True)
class PatternExtractionRequest:

    experience: DecisionExperience
    features: Mapping[str, Any]
    pattern_type: str

    def __post_init__(self) -> None:
        if not isinstance(self.features, Mapping):
            raise TypeError(
                "features must be a mapping"
            )

        if not self.pattern_type.strip():
            raise ValueError(
                "pattern_type must not be empty"
            )


class DecisionPatternExtractor:
    """
    Converts validated experiences into decision patterns.

    Does not:
    - modify experiences
    - execute decisions
    - create adaptations
    """

    def extract(
        self,
        request: PatternExtractionRequest,
    ) -> DecisionPattern:

        return DecisionPattern(
            pattern_id=str(uuid4()),
            source_experience_id=(
                request.experience.experience_id
            ),
            pattern_type=request.pattern_type.strip(),
            features=dict(request.features),
        )