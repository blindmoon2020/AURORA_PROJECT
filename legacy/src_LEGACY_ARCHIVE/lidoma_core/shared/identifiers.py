from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class EntityId:

    value: str


    @classmethod
    def generate(
        cls,
    ) -> "EntityId":

        return cls(
            value=str(uuid4())
        )


    def __post_init__(self):

        if not self.value.strip():
            raise ValueError(
                "entity id must not be empty"
            )