from dataclasses import dataclass
from typing import Literal


RuntimeState = Literal[
    "INITIALIZED",
    "VALIDATED",
    "APPROVED",
    "BLOCKED",
]


@dataclass(frozen=True)
class FinancialRuntimeContract:

    module_name: str

    state: RuntimeState

    production_ready: bool = False


    def __post_init__(self):

        if not self.module_name.strip():
            raise ValueError(
                "module_name must not be empty"
            )

        if self.state not in (
            "INITIALIZED",
            "VALIDATED",
            "APPROVED",
            "BLOCKED",
        ):
            raise ValueError(
                "invalid runtime state"
            )