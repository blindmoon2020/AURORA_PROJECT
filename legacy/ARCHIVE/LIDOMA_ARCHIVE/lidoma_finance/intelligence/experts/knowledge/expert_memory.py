from typing import Dict, Any



class ExpertMemory:
    """
    Persistent expert reasoning memory abstraction.
    """


    def __init__(self):

        self._memory: Dict[
            str,
            list
        ] = {}



    def store(
        self,
        expert_id: str,
        data: Dict[str, Any],
    ):

        self._memory.setdefault(

            expert_id,

            []

        ).append(

            data

        )



    def recall(
        self,
        expert_id: str,
    ):

        return self._memory.get(

            expert_id,

            []

        )