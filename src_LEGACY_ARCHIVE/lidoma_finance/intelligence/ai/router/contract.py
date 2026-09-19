from abc import ABC, abstractmethod
from typing import Any


class AIRouter(ABC):
    """
    Contract for multi AI routing.
    """


    @abstractmethod
    def route(
        self,
        context: Any,
        **kwargs,
    ) -> Any:
        pass