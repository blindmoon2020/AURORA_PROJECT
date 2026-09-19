from abc import ABC, abstractmethod
from typing import Any


class AIProviderAdapter(ABC):
    """
    Base contract for external AI providers.
    """


    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass


    @property
    @abstractmethod
    def capabilities(self) -> list[str]:
        pass


    @abstractmethod
    def generate(
        self,
        context: Any,
        **kwargs,
    ) -> Any:
        pass


    @abstractmethod
    def health_check(self) -> bool:
        pass