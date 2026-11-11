from abc import (
    ABC,
    abstractmethod,
)


from .request import ConsensusRequest

from .response import ConsensusResponse



class ConsensusContract(
    ABC
):
    """
    Abstract contract for consensus reasoning engines.
    """


    @abstractmethod
    def evaluate(
        self,
        request: ConsensusRequest,
    ) -> ConsensusResponse:
        """
        Evaluate multiple AI responses
        and produce consensus output.
        """

        raise NotImplementedError
