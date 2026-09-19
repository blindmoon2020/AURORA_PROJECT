"""
Financial decision risk model.
"""


from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class DecisionRisk:
    """
    Represents financial decision risk level.
    """


    score: float


    category: str


    def is_high(
        self,
    ) -> bool:
        """
        Evaluate high risk state.
        """

        return self.score >= 0.8