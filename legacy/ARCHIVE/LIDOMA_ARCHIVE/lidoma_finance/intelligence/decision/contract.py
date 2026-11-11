"""
Financial Decision Layer Contracts.

Defines abstract contracts for
financial decision processing.
"""


from abc import (
    ABC,
    abstractmethod,
)


from .request import (
    DecisionRequest,
)


from .response import (
    DecisionResponse,
)



class FinancialDecisionContract(
    ABC
):
    """
    Abstract contract for financial decision engines.
    """


    @abstractmethod
    def decide(
        self,
        request: DecisionRequest,
    ) -> DecisionResponse:
        """
        Execute financial decision process.
        """

        raise NotImplementedError