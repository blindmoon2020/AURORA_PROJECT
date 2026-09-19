from dataclasses import (
    dataclass,
    field,
)


from typing import (
    Dict,
    Any,
)


from .identity import (
    ExpertIdentity,
)



@dataclass(
    frozen=True
)
class ExpertProfile:
    """
    Complete expert intelligence profile.
    """


    identity: ExpertIdentity


    methodology: str


    specialization: list[str] = field(
        default_factory=list
    )


    metadata: Dict[str, Any] = field(
        default_factory=dict
    )