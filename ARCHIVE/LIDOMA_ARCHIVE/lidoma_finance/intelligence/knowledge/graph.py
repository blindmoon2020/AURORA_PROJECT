from dataclasses import dataclass, field


@dataclass
class KnowledgeGraph:
    """
    Relationship graph for financial intelligence.
    """


    nodes: dict[str, dict] = field(
        default_factory=dict
    )


    relations: list[tuple] = field(
        default_factory=list
    )


    def add_node(
        self,
        node_id: str,
        data: dict,
    ):

        self.nodes[node_id] = data


    def add_relation(
        self,
        source: str,
        target: str,
        relation: str,
    ):

        self.relations.append(
            (
                source,
                target,
                relation,
            )
        )