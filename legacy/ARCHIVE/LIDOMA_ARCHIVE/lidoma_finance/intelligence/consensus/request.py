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
class ConsensusRequest:
    """
    Input model for consensus reasoning.
    """


    request_id: str

    query: str


    providers: List[str] = field(
        default_factory=list
    )


    context: Dict[str, Any] = field(
        default_factory=dict
    )


    metadata: Dict[str, Any] = field(
        default_factory=dict
    )