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
class ExpertRequest:
    """
    Input request for expert analysis.
    """


    request_id: str


    topic: str


    experts: List[str] = field(
        default_factory=list
    )


    context: Dict[str, Any] = field(
        default_factory=dict
    )