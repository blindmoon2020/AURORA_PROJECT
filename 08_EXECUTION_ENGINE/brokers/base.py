from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Sequence

from core.contracts import BarRecord, QuoteSnapshot, SymbolSpec


class BrokerGateway(ABC):
    """
    Broker abstraction.

    Strategy-facing interface uses canonical symbols only.

    Execution is disabled during architecture-v2.
    """

    broker_id: str

    @abstractmethod
    def connect(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_symbols(self) -> Sequence[str]:
        raise NotImplementedError

    @abstractmethod
    def get_symbol_spec(
        self,
        canonical_symbol: str,
    ) -> SymbolSpec:
        raise NotImplementedError

    @abstractmethod
    def get_quote(
        self,
        canonical_symbol: str,
    ) -> QuoteSnapshot:
        raise NotImplementedError

    @abstractmethod
    def get_bars(
        self,
        canonical_symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[BarRecord]:
        raise NotImplementedError

    def execution_enabled(self) -> bool:
        return False

    def place_order(self, *args, **kwargs):
        raise RuntimeError(
            "AURORA execution is disabled in architecture-v2."
        )
