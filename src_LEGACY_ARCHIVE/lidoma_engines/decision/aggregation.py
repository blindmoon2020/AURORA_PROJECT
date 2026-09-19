from .evidence import (
    DecisionEvidence,
    EvidenceAggregate,
    EvidenceDirection,
)


class EvidenceAggregator:
    """
    Deterministic Phase 6.1 aggregation.

    This class intentionally remains provider-agnostic and correlation-unaware.
    Phase 6.2 correlation/reliability logic lives in ConsensusEngine, preserving
    the Phase 6.1 contract and allowing controlled comparison between the two
    paths.
    """

    def aggregate(
        self,
        evidence: tuple[DecisionEvidence, ...],
    ) -> EvidenceAggregate:
        bullish_weight = 0.0
        bearish_weight = 0.0
        neutral_weight = 0.0
        unknown_weight = 0.0
        usable_evidence_count = 0

        for item in evidence:
            effective_weight = item.quality.effective_weight

            if effective_weight > 0.0:
                usable_evidence_count += 1

            if item.direction == EvidenceDirection.BULLISH:
                bullish_weight += effective_weight
            elif item.direction == EvidenceDirection.BEARISH:
                bearish_weight += effective_weight
            elif item.direction == EvidenceDirection.NEUTRAL:
                neutral_weight += effective_weight
            else:
                unknown_weight += effective_weight

        directional_total = bullish_weight + bearish_weight

        total_weight = (
            directional_total
            + neutral_weight
            + unknown_weight
        )

        if directional_total > 0.0:
            direction_score = (
                bullish_weight - bearish_weight
            ) / directional_total

            agreement_ratio = abs(
                bullish_weight - bearish_weight
            ) / directional_total

            conflict_ratio = 1.0 - agreement_ratio
        else:
            direction_score = 0.0
            agreement_ratio = 0.0
            conflict_ratio = 0.0

        if total_weight > 0.0:
            directional_coverage = directional_total / total_weight
            confidence = agreement_ratio * directional_coverage
        else:
            confidence = 0.0

        return EvidenceAggregate(
            evidence_ids=tuple(item.evidence_id for item in evidence),
            source_ids=tuple(
                dict.fromkeys(item.source_id for item in evidence)
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
