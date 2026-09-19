from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Provenance:

    source: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def __post_init__(self):

        if not self.source.strip():
            raise ValueError(
                "provenance source must not be empty"
            )