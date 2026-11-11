from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RiskMetric:

    name: str

    value: float

    metadata: dict[str, Any]


    def __post_init__(self):

        if not self.name.strip():
            raise ValueError(
                "name must not be empty"
            )