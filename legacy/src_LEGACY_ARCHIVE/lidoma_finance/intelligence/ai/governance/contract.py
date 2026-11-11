from abc import ABC, abstractmethod
from typing import Any


class ProviderGovernanceContract(ABC):
    """
    Root contract for AI provider governance.
    """


    @abstractmethod
    def validate(
        self,
        provider: Any,
    ) -> bool:
        pass