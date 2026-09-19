from abc import ABC, abstractmethod
from typing import Any


class DataNormalizer(ABC):
    """
    Universal contract for converting
    external raw data into LIDOMA canonical format.
    """


    @property
    @abstractmethod
    def normalizer_id(self) -> str:
        pass


    @property
    @abstractmethod
    def supported_type(self) -> str:
        pass


    @abstractmethod
    def normalize(
        self,
        data: Any,
        **kwargs: Any,
    ) -> Any:
        pass