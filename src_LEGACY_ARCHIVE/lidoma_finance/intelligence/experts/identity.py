from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class ExpertIdentity:
    """
    Unique expert identity model.
    """


    expert_id: str

    name: str

    organization: str

    domain: str