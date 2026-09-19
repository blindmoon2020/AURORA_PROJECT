from abc import ABC, abstractmethod


class CredentialResolver(ABC):
    """
    Secure credential resolution contract.
    """


    @abstractmethod
    def resolve(
        self,
        key_reference: str,
    ) -> str:
        pass