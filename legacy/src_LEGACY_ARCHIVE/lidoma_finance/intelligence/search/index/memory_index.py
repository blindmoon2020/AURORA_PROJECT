class MemorySearchIndex:
    """
    In-memory search index foundation.
    """


    def __init__(self):

        self.documents = {}


    def add(
        self,
        document_id: str,
        document,
    ):

        self.documents[
            document_id
        ] = document


    def get_all(self):

        return list(
            self.documents.items()
        )