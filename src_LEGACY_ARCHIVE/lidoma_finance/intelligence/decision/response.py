"""
LIDOMA Financial Decision Response Model.

Canonical response contract for
financial decision intelligence runtime.
"""


from dataclasses import (
    dataclass,
    field,
)


from typing import (
    Dict,
    Any,
)


from .state import (
    DecisionState,
)



@dataclass(
    frozen=True
)
class DecisionResponse:
    """
    Final financial decision response.
    """


    decision_id: str


    state: DecisionState


    recommendation: str


    confidence: float = 0.0


    evidence: Dict[str, Any] = field(
        default_factory=dict
    )


    metadata: Dict[str, Any] = field(
        default_factory=dict
    )