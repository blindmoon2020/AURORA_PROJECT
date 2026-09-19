from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CorporateAction:

    symbol: str

    action_type: str

    effective_date: datetime


    def __post_init__(self):

        if not self.symbol.strip():
            raise ValueError(
                "symbol must not be empty"
            )

        if not self.action_type.strip():
            raise ValueError(
                "action_type must not be empty"
            )

        if (
            self.effective_date.tzinfo is None
            or self.effective_date.utcoffset() is None
        ):
            raise ValueError(
                "effective_date must be timezone-aware"
            )