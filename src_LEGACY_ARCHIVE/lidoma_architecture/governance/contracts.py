from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContractDescriptor:

    name: str

    version: str

    owner: str

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


    def __post_init__(self):

        if not self.name.strip():
            raise ValueError(
                "contract name required"
            )

        if not self.version.strip():
            raise ValueError(
                "contract version required"
            )

        if not self.owner.strip():
            raise ValueError(
                "contract owner required"
            )