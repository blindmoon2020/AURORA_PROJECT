from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class LIDOMAErrorRecord:
    error_id: str
    component: str
    error_type: str
    message: str

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not isinstance(self.error_id, str):
            raise TypeError(
                "error_id must be a string"
            )

        if not isinstance(self.component, str):
            raise TypeError(
                "component must be a string"
            )

        if not isinstance(self.error_type, str):
            raise TypeError(
                "error_type must be a string"
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "message must be a string"
            )

        if not self.error_id.strip():
            raise ValueError(
                "error_id must not be empty"
            )

        if not self.component.strip():
            raise ValueError(
                "component must not be empty"
            )

        if not self.error_type.strip():
            raise ValueError(
                "error_type must not be empty"
            )

        if not self.message.strip():
            raise ValueError(
                "message must not be empty"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )