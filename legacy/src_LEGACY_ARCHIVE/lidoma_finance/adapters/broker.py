from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class BrokerConnection:

    broker_id: str

    name: str

    environment: str

    connected_at: datetime


    def __post_init__(self):

        if not self.broker_id.strip():
            raise ValueError(
                "broker_id must not be empty"
            )

        if not self.name.strip():
            raise ValueError(
                "broker name must not be empty"
            )

        if not self.environment.strip():
            raise ValueError(
                "environment must not be empty"
            )

        if (
            self.connected_at.tzinfo is None
            or self.connected_at.utcoffset() is None
        ):
            raise ValueError(
                "connected_at must be timezone-aware"
            )