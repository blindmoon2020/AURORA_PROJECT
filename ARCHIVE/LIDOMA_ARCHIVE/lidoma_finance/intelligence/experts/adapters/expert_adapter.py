from abc import ABC, abstractmethod


class ExpertAdapter(ABC):
    """
    Abstract adapter for external expert sources.
    """


    @abstractmethod
    def analyze(self, request):
        raise NotImplementedError