from abc import (
    ABC,
    abstractmethod,
)



class RuntimeComponent(
    ABC
):
    """
    Standard runtime component interface.
    """


    @abstractmethod
    def execute(
        self,
        *args,
        **kwargs,
    ):
        raise NotImplementedError



    def validate_contract(
        self,
    ) -> bool:

        return True