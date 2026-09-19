from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class SimulationResult:

    simulation_id: str

    strategy_id: str

    total_trades: int

    winning_trades: int

    losing_trades: int

    net_return: float

    created_at: datetime


    def __post_init__(self):

        if not self.simulation_id.strip():
            raise ValueError(
                "simulation_id must not be empty"
            )

        if not self.strategy_id.strip():
            raise ValueError(
                "strategy_id must not be empty"
            )

        if self.total_trades < 0:
            raise ValueError(
                "total_trades cannot be negative"
            )

        if (
            self.created_at.tzinfo is None
            or self.created_at.utcoffset() is None
        ):
            raise ValueError(
                "created_at must be timezone-aware"
            )