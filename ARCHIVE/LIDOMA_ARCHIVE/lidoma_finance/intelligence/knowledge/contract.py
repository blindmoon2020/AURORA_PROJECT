from abc import ABC, abstractmethod
from typing import Any


class KnowledgeStore(ABC):
    """
    Contract for LIDOMA knowledge storage systems.
    """


    @abstractmethod
    def save(
        self,
        entity: Any,
    ) -> None:
        pass


    @abstractmethod
    def get(
        self,
        entity_id: str,
    ) -> Any:
        pass


    @abstractmethod
    def search(
        self,
        query: str,
    ) -> list[Any]:
        pass