from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Signal:

    symbol: str

    timeframe: str

    direction: str

    entry: float

    stop_loss: float

    take_profit: float


    score: float

    status: str


    created_at: datetime


    def is_trade_candidate(self):

        return self.status == "TRADE_CANDIDATE"