from abc import ABC, abstractmethod
from typing import Any


class SearchProvider(ABC):
    """
    Universal contract for LIDOMA intelligent search providers.
    """


    @property
    @abstractmethod
    def search_id(self) -> str:
        pass


    @abstractmethod
    def search(
        self,
        query: str,
        **kwargs: Any,
    ) -> list[Any]:
        pass