from abc import (
    ABC,
    abstractmethod,
)



class ArchitectureContract(
    ABC
):
    """
    Base governance contract.

    Every runtime component must
    expose a compatible contract.
    """


    @abstractmethod
    def validate_contract(
        self,
    ) -> bool:
        """
        Runtime compatibility check.
        """

        raise NotImplementedError