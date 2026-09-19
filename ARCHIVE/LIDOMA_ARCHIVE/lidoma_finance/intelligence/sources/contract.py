from abc import ABC, abstractmethod
from typing import Any


class SourceAdapter(ABC):
    """
    Universal external source adapter contract.
    """


    @property
    @abstractmethod
    def source_id(self) -> str:
        pass


    @property
    @abstractmethod
    def source_type(self) -> str:
        pass


    @abstractmethod
    def collect(
        self,
        **kwargs: Any,
    ) -> Any:
        pass