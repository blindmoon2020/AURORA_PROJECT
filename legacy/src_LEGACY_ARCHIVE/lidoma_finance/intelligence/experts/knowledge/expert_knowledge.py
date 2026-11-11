from dataclasses import dataclass, field


@dataclass
class ExpertKnowledge:
    """
    Stores expert generated knowledge.
    """


    expert_id: str

    topic: str

    content: str

    metadata: dict = field(
        default_factory=dict
    )