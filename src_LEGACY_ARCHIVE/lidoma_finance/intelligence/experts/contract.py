from abc import (
    ABC,
    abstractmethod,
)


from .request import (
    ExpertRequest,
)



class ExpertIntelligenceContract(
    ABC
):
    """
    Abstract contract for expert intelligence providers.
    """


    @abstractmethod
    def analyze(
        self,
        request: ExpertRequest,
    ):
        """
        Execute expert analysis.
        """

        raise NotImplementedError