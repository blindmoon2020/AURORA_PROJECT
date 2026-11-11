from ..knowledge import (
    ExpertKnowledgeRepository,
)

from ..memory import (
    ExpertMemoryStore,
)



class ExpertIntegrationAdapter:
    """
    Connects expert knowledge,
    memory and runtime.
    """



    def __init__(
        self,
        knowledge_repository=None,
        memory_store=None,
    ):

        self.knowledge = (
            knowledge_repository
            or ExpertKnowledgeRepository()
        )

        self.memory = (
            memory_store
            or ExpertMemoryStore()
        )



    def register_knowledge(
        self,
        expert_id: str,
        knowledge,
    ):

        self.knowledge.store(
            expert_id,
            knowledge,
        )



    def remember(
        self,
        record,
    ):

        self.memory.add(
            record
        )