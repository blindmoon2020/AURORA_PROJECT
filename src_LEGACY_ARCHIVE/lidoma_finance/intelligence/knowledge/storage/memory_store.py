from ..entity import KnowledgeEntity


class MemoryKnowledgeStore:
    """
    In-memory knowledge storage.
    """


    def __init__(self):

        self.data = {}


    def save(
        self,
        entity: KnowledgeEntity,
    ):

        self.data[
            entity.entity_id
        ] = entity


    def get(
        self,
        entity_id: str,
    ):

        return self.data.get(
            entity_id
        )


    def search(
        self,
        query: str,
    ):

        return [

            entity

            for entity in self.data.values()

            if query.lower()
            in str(entity.content).lower()

        ]