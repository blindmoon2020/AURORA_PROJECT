from dataclasses import dataclass
from datetime import time
from enum import Enum
from typing import Tuple


class SessionType(str, Enum):
    """
    Global trading session categories.
    """

    SYDNEY = "SYDNEY"
    TOKYO = "TOKYO"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    GLOBAL = "GLOBAL"


@dataclass(frozen=True)
class TradingSession:
    """
    Represents a trading time window.

    Examples:

    Forex:
        London Session
        New York Session

    Crypto:
        Global 24/7 Session

    Stock:
        Exchange opening hours
    """

    name: str

    session_type: SessionType

    timezone: str

    open_time: time

    close_time: time

    active_days: Tuple[str, ...]

    def __post_init__(self):

        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Session name cannot be empty"
            )

        object.__setattr__(
            self,
            "name",
            normalized_name
        )

        if not self.timezone.strip():
            raise ValueError(
                "Timezone cannot be empty"
            )

        if not self.active_days:
            raise ValueError(
                "Active days cannot be empty"
            )

    def is_active_day(self, day: str) -> bool:
        """
        Check whether session is active on a day.
        """

        return day.upper() in (
            item.upper()
            for item in self.active_days
        )