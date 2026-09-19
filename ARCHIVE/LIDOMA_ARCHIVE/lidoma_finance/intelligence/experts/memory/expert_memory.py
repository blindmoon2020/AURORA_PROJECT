class ExpertMemory:
    """
    Runtime memory for expert intelligence.
    """


    def __init__(self):

        self._records = []


    def store(
        self,
        knowledge,
    ):

        self._records.append(
            knowledge
        )


    def retrieve_all(
        self,
    ):

        return self._records.copy()