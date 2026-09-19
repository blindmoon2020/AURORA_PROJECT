from dataclasses import dataclass



@dataclass(frozen=True)
class ExpertKnowledgeSource:
    """
    Expert knowledge source metadata.
    """


    source_id: str

    expert_id: str

    title: str

    category: str