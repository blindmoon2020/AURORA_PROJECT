from dataclasses import dataclass
from typing import Mapping

from .correlation import (
    EvidenceCluster,
    EvidenceCorrelationClusterer,
)
from .evidence import (
    DecisionEvidence,
    EvidenceAggregate,
    EvidenceDirection,
)
from .governance import GovernedEvidence
from .reliability import ReliabilityResolver


@dataclass(frozen=True)
class ConsensusResult:
    aggregate: EvidenceAggregate
    clusters: tuple[EvidenceCluster, ...]
    independent_cluster_count: int
    usable_cluster_count: int
    correlated_cluster_count: int
    raw_effective_weight: float
    adjusted_effective_weight: float
    duplication_discount_ratio: float

    def __post_init__(self) -> None:
        for name, value in (
            (
                "independent_cluster_count",
                self.independent_cluster_count,
            ),
            (
                "usable_cluster_count",
                self.usable_cluster_count,
            ),
            (
                "correlated_cluster_count",
                self.correlated_cluster_count,
            ),
        ):
            if value < 0:
                raise ValueError(
                    f"{name} must not be negative"
                )

        if self.usable_cluster_count > self.independent_cluster_count:
            raise ValueError(
                "usable_cluster_count must be <= independent_cluster_count"
            )

        if self.correlated_cluster_count > self.independent_cluster_count:
            raise ValueError(
                "correlated_cluster_count must be <= "
                "independent_cluster_count"
            )

        if self.raw_effective_weight < 0.0:
            raise ValueError(
                "raw_effective_weight must not be negative"
            )

        if self.adjusted_effective_weight < 0.0:
            raise ValueError(
                "adjusted_effective_weight must not be negative"
            )

        if not 0.0 <= self.duplication_discount_ratio <= 1.0:
            raise ValueError(
                "duplication_discount_ratio must be between 0 and 1"
            )


class ConsensusEngine:
    """
    Correlation-aware, reliability-aware, and optionally governance-aware
    deterministic consensus engine.

    Phase 6.2 compatibility:
    evaluate(evidence) preserves the original consensus behavior by assigning
    every evidence item a freshness modifier of 1.0.

    Phase 6.3.2:
    evaluate_governed(governed_evidence) excludes rejected evidence and applies
    deterministic freshness factors before correlation adjustment.

    Weighting order:
    1. confidence
    2. resolved reliability
    3. configured evidence weight
    4. freshness modifier
    5. correlation duplication cap
    """

    def __init__(
        self,
        *,
        reliability_resolver: ReliabilityResolver | None = None,
        clusterer: EvidenceCorrelationClusterer | None = None,
    ) -> None:
        self.reliability_resolver = reliability_resolver
        self.clusterer = (
            clusterer
            or EvidenceCorrelationClusterer()
        )

    def evaluate(
        self,
        evidence: tuple[DecisionEvidence, ...],
    ) -> ConsensusResult:
        """
        Backward-compatible Phase 6.2 path.

        Freshness is deliberately not inferred here. Existing callers retain
        the exact Phase 6.2 weighting contract.
        """
        return self._evaluate(
            evidence=evidence,
            freshness_factors={},
        )

    def evaluate_governed(
        self,
        governed_evidence: tuple[GovernedEvidence, ...],
    ) -> ConsensusResult:
        """
        Phase 6.3.2 governance-aware consensus path.

        Rejected evidence is excluded from clustering and weighting.
        Accepted stale evidence participates with its deterministic freshness
        factor.
        """
        accepted = tuple(
            item
            for item in governed_evidence
            if item.is_accepted
        )

        evidence = tuple(
            item.evidence
            for item in accepted
        )

        freshness_factors = {
            item.evidence.evidence_id: item.freshness_factor
            for item in accepted
        }

        return self._evaluate(
            evidence=evidence,
            freshness_factors=freshness_factors,
        )

    def _evaluate(
        self,
        *,
        evidence: tuple[DecisionEvidence, ...],
        freshness_factors: Mapping[str, float],
    ) -> ConsensusResult:
        evidence_ids = [
            item.evidence_id
            for item in evidence
        ]

        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError(
                "consensus evidence IDs must be unique"
            )

        unknown_modifier_ids = (
            set(freshness_factors)
            - set(evidence_ids)
        )

        if unknown_modifier_ids:
            raise ValueError(
                "freshness factors contain unknown evidence IDs"
            )

        for evidence_id, factor in freshness_factors.items():
            if not 0.0 <= factor <= 1.0:
                raise ValueError(
                    "freshness factor must be between 0 and 1 "
                    f"for evidence '{evidence_id}'"
                )

        clusters = self.clusterer.cluster(evidence)

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence
        }

        bullish_weight = 0.0
        bearish_weight = 0.0
        neutral_weight = 0.0
        unknown_weight = 0.0

        raw_effective_weight = 0.0
        adjusted_effective_weight = 0.0
        usable_evidence_count = 0
        usable_cluster_count = 0
        correlated_cluster_count = 0

        for cluster in clusters:
            weighted_items: list[
                tuple[DecisionEvidence, float]
            ] = []

            for evidence_id in cluster.evidence_ids:
                item = evidence_by_id[evidence_id]

                resolved_reliability = (
                    item.quality.reliability
                )

                if self.reliability_resolver is not None:
                    resolved_reliability = (
                        self.reliability_resolver.resolve(
                            item.source_id,
                            item.capability,
                            item.quality.reliability,
                        )
                    )

                freshness_factor = freshness_factors.get(
                    item.evidence_id,
                    1.0,
                )

                raw_weight = (
                    item.quality.confidence
                    * resolved_reliability
                    * item.quality.weight
                    * freshness_factor
                )

                raw_effective_weight += raw_weight

                if raw_weight > 0.0:
                    usable_evidence_count += 1

                weighted_items.append(
                    (
                        item,
                        raw_weight,
                    )
                )

            positive_weights = tuple(
                raw_weight
                for _, raw_weight in weighted_items
                if raw_weight > 0.0
            )

            if not positive_weights:
                continue

            usable_cluster_count += 1

            if cluster.is_correlated:
                correlated_cluster_count += 1

            cluster_raw_total = sum(
                positive_weights
            )

            if cluster.is_correlated:
                cluster_budget = max(
                    positive_weights
                )
                scale = (
                    cluster_budget
                    / cluster_raw_total
                )
            else:
                scale = 1.0

            for item, raw_weight in weighted_items:
                adjusted_weight = (
                    raw_weight
                    * scale
                )

                adjusted_effective_weight += (
                    adjusted_weight
                )

                if item.direction == EvidenceDirection.BULLISH:
                    bullish_weight += adjusted_weight
                elif item.direction == EvidenceDirection.BEARISH:
                    bearish_weight += adjusted_weight
                elif item.direction == EvidenceDirection.NEUTRAL:
                    neutral_weight += adjusted_weight
                else:
                    unknown_weight += adjusted_weight

        directional_total = (
            bullish_weight
            + bearish_weight
        )

        total_weight = (
            directional_total
            + neutral_weight
            + unknown_weight
        )

        if directional_total > 0.0:
            direction_score = (
                bullish_weight
                - bearish_weight
            ) / directional_total

            agreement_ratio = abs(
                bullish_weight
                - bearish_weight
            ) / directional_total

            conflict_ratio = (
                1.0
                - agreement_ratio
            )
        else:
            direction_score = 0.0
            agreement_ratio = 0.0
            conflict_ratio = 0.0

        if total_weight > 0.0:
            directional_coverage = (
                directional_total
                / total_weight
            )

            confidence = (
                agreement_ratio
                * directional_coverage
            )
        else:
            confidence = 0.0

        if raw_effective_weight > 0.0:
            duplication_discount_ratio = max(
                0.0,
                min(
                    1.0,
                    1.0
                    - (
                        adjusted_effective_weight
                        / raw_effective_weight
                    ),
                ),
            )
        else:
            duplication_discount_ratio = 0.0

        aggregate = EvidenceAggregate(
            evidence_ids=tuple(
                item.evidence_id
                for item in evidence
            ),
            source_ids=tuple(
                dict.fromkeys(
                    item.source_id
                    for item in evidence
                )
            ),
            bullish_weight=bullish_weight,
            bearish_weight=bearish_weight,
            neutral_weight=neutral_weight,
            unknown_weight=unknown_weight,
            direction_score=direction_score,
            agreement_ratio=agreement_ratio,
            conflict_ratio=conflict_ratio,
            confidence=confidence,
            usable_evidence_count=usable_evidence_count,
            total_evidence_count=len(evidence),
        )

        return ConsensusResult(
            aggregate=aggregate,
            clusters=clusters,
            independent_cluster_count=len(clusters),
            usable_cluster_count=usable_cluster_count,
            correlated_cluster_count=correlated_cluster_count,
            raw_effective_weight=raw_effective_weight,
            adjusted_effective_weight=adjusted_effective_weight,
            duplication_discount_ratio=duplication_discount_ratio,
        )