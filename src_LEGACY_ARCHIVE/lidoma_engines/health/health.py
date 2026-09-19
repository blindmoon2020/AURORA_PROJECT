from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class HealthStatus:

    component: str

    healthy: bool

    checks: dict[str, bool] = field(
        default_factory=dict
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


    def __post_init__(self):

        if not self.component.strip():
            raise ValueError(
                "component must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )