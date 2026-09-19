from dataclasses import dataclass, field

from .entity import KnowledgeEntity


@dataclass
class IntelligenceMemory:
    """
    Runtime memory for intelligence entities.
    """


    records: dict[str, KnowledgeEntity] = field(
        default_factory=dict
    )


    def store(
        self,
        entity: KnowledgeEntity,
    ):

        self.records[
            entity.entity_id
        ] = entity


    def retrieve(
        self,
        entity_id: str,
    ) -> KnowledgeEntity:

        return self.records[
            entity_id
        ]


    def all(self):

        return list(
            self.records.values()
        )