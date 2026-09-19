from typing import List, Dict, Any



class ExpertMemoryStore:
    """
    Historical expert decision memory.
    """


    def __init__(self):

        self._records: List[Dict[str, Any]] = []



    def add(
        self,
        record: Dict[str, Any],
    ) -> None:

        self._records.append(
            record
        )



    def all(
        self,
    ) -> List[Dict[str, Any]]:

        return list(
            self._records
        )



    def count(
        self,
    ) -> int:

        return len(
            self._records
        )