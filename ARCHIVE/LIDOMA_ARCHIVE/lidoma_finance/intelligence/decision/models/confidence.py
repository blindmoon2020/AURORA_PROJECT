from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class DecisionConfidence:
    """
    Decision confidence evaluation.
    """


    score: float


    explanation: str


    def is_valid(
        self,
    ) -> bool:

        return 0 <= self.score <= 1