from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Metadata:

    values: dict[str, Any] = field(
        default_factory=dict
    )


    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.values.get(
            key,
            default,
        )