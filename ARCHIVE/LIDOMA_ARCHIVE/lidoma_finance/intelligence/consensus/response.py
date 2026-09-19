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
class ConsensusResponse:
    """
    Canonical consensus result.
    """


    request_id: str


    final_answer: str


    participating_providers: List[str] = field(
        default_factory=list
    )


    evidence: Dict[str, Any] = field(
        default_factory=dict
    )


    metadata: Dict[str, Any] = field(
        default_factory=dict
    )