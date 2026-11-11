from abc import ABC, abstractmethod
from typing import Any


class ContextBuilder(ABC):
    """
    Contract for building AI reasoning contexts.
    """


    @abstractmethod
    def build(
        self,
        **kwargs: Any,
    ) -> Any:
        pass