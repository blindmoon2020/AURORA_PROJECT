from abc import ABC, abstractmethod



class ExpertKnowledgeContract(ABC):
    """
    Contract for expert knowledge providers.
    """


    @abstractmethod
    def retrieve(
        self,
        query: str,
    ):
        """
        Retrieve expert knowledge.
        """

        raise NotImplementedError