from abc import ABC, abstractmethod
from typing import Any


class MarketDataProvider(ABC):
    """
    Abstract contract for all market data providers.
    """


    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass


    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


    @abstractmethod
    def connect(self) -> bool:
        pass


    @abstractmethod
    def disconnect(self) -> bool:
        pass


    @abstractmethod
    def get_market_data(
        self,
        symbol: str,
        **kwargs: Any,
    ) -> Any:
        pass