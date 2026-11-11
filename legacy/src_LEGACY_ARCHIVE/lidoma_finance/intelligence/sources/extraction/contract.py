from abc import ABC, abstractmethod
from typing import Any


class DataExtractor(ABC):
    """
    Universal contract for extracting
    data from validated sources.
    """


    @property
    @abstractmethod
    def extractor_id(self) -> str:
        pass


    @property
    @abstractmethod
    def source_type(self) -> str:
        pass


    @abstractmethod
    def extract(
        self,
        source_id: str,
        **kwargs: Any,
    ) -> Any:
        pass