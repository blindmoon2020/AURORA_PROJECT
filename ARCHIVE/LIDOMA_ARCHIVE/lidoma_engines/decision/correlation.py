from dataclasses import dataclass

from .evidence import DecisionEvidence


@dataclass(frozen=True)
class EvidenceCluster:
    cluster_id: str
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    dependency_keys: tuple[str, ...]

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_ids)

    @property
    def is_correlated(self) -> bool:
        return self.evidence_count > 1


class EvidenceCorrelationClusterer:
    """
    Builds transitive dependency clusters from explicit evidence lineage.

    Rules:
    - Evidence sharing at least one dependency key belongs to the same connected
      component.
    - Dependency is transitive:
      A shares X with B, and B shares Y with C => A/B/C are one cluster.
    - Evidence without dependency keys is independent and becomes its own
      cluster.
    - Provider identity alone does not imply correlation.
    """

    def cluster(
        self,
        evidence: tuple[DecisionEvidence, ...],
    ) -> tuple[EvidenceCluster, ...]:
        if not evidence:
            return ()

        parent = list(range(len(evidence)))
        rank = [0] * len(evidence)

        def find(index: int) -> int:
            if parent[index] != index:
                parent[index] = find(parent[index])
            return parent[index]

        def union(left: int, right: int) -> None:
            left_root = find(left)
            right_root = find(right)

            if left_root == right_root:
                return

            if rank[left_root] < rank[right_root]:
                parent[left_root] = right_root
            elif rank[left_root] > rank[right_root]:
                parent[right_root] = left_root
            else:
                parent[right_root] = left_root
                rank[left_root] += 1

        dependency_owner: dict[str, int] = {}

        for index, item in enumerate(evidence):
            for dependency_key in item.dependency_keys:
                previous = dependency_owner.get(dependency_key)

                if previous is None:
                    dependency_owner[dependency_key] = index
                else:
                    union(previous, index)

        grouped: dict[int, list[int]] = {}

        for index in range(len(evidence)):
            root = find(index)
            grouped.setdefault(root, []).append(index)

        clusters: list[EvidenceCluster] = []

        for cluster_number, indexes in enumerate(
            grouped.values(),
            start=1,
        ):
            items = tuple(evidence[index] for index in indexes)

            clusters.append(
                EvidenceCluster(
                    cluster_id=f"cluster-{cluster_number}",
                    evidence_ids=tuple(
                        item.evidence_id for item in items
                    ),
                    source_ids=tuple(
                        dict.fromkeys(
                            item.source_id for item in items
                        )
                    ),
                    dependency_keys=tuple(
                        dict.fromkeys(
                            dependency_key
                            for item in items
                            for dependency_key in item.dependency_keys
                        )
                    ),
                )
            )

        return tuple(clusters)
