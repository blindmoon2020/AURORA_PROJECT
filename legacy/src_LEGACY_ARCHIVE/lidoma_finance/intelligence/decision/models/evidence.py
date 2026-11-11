from dataclasses import (
    dataclass,
    field,
)


from typing import (
    List,
)



@dataclass(
    frozen=True
)
class DecisionEvidence:
    """
    Evidence aggregation model.
    """


    sources: List[str] = field(
        default_factory=list
    )


    reliability_score: float = 0.0