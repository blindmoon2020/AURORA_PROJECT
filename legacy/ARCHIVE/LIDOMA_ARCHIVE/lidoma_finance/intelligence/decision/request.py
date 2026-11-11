"""
Financial Decision Request Models.

Defines canonical input contracts
for decision intelligence layer.
"""


from dataclasses import (
    dataclass,
    field,
)

from typing import (
    Dict,
    Any,
    List,
)



@dataclass(
    frozen=True
)
class DecisionRequest:
    """
    Base decision request contract.
    """


    request_id: str

    objective: str


    context: Dict[str, Any] = field(
        default_factory=dict
    )



@dataclass(
    frozen=True
)
class FinancialDecisionRequest:
    """
    Financial intelligence decision request.
    """


    request_id: str

    asset: str

    objective: str


    signals: List[str] = field(
        default_factory=list
    )


    context: Dict[str, Any] = field(
        default_factory=dict
    )