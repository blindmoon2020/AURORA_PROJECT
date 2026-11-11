from typing import Dict, Any



class ExpertKnowledgeRepository:
    """
    Storage abstraction for expert knowledge.
    """


    def __init__(self):

        self._knowledge: Dict[str, Any] = {}



    def store(
        self,
        expert_id: str,
        knowledge: Any,
    ) -> None:

        self._knowledge[expert_id] = knowledge



    def retrieve(
        self,
        expert_id: str,
    ) -> Any:

        return self._knowledge.get(
            expert_id
        )



    def exists(
        self,
        expert_id: str,
    ) -> bool:

        return expert_id in self._knowledge