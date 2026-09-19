from typing import List


from .source import (
    ExpertKnowledgeSource,
)



class ExpertKnowledgeBase:
    """
    Expert knowledge storage layer.
    """


    def __init__(self):

        self._sources: List[
            ExpertKnowledgeSource
        ] = []



    def register(
        self,
        source: ExpertKnowledgeSource,
    ):

        self._sources.append(
            source
        )



    def search(
        self,
        expert_id: str,
    ):

        return [

            source

            for source in self._sources

            if source.expert_id == expert_id

        ]