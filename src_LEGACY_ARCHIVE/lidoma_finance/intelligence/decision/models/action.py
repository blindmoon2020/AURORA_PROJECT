from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class DecisionAction:
    """
    Financial decision action model.
    """


    symbol: str


    action: str


    timeframe: str


    rationale: str