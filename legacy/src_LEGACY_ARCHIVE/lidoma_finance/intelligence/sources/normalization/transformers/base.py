from abc import ABC, abstractmethod
from typing import Any


class DataTransformer(ABC):
    """
    Base transformer for source-specific conversion.
    """


    @abstractmethod
    def transform(
        self,
        data: Any,
    ) -> Any:
        pass