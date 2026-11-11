from dataclasses import (
    dataclass,
    field,
)


from typing import (
    Dict,
    Any,
)



@dataclass(
    frozen=True
)
class DecisionContext:
    """
    Runtime context for financial decisions.
    """


    decision_id: str


    trace_id: str


    confidence: float = 0.0


    metadata: Dict[str, Any] = field(
        default_factory=dict
    )