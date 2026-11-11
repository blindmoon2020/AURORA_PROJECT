from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):


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
        prompt: str,
        context: Any = None,
    ) -> Any:
        pass