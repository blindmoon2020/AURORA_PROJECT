from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class DecisionRisk:
    """
    Risk assessment model.
    """


    level: str


    score: float


    description: str