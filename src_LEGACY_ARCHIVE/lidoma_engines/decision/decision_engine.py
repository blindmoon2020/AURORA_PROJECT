from dataclasses import dataclass
from datetime import datetime

from .aggregation import EvidenceAggregator
from .consensus import ConsensusEngine, ConsensusResult
from .decision import Decision, DecisionAction
from .decision_context import DecisionContext
from .decision_score import DecisionScore
from .evidence import (
    DecisionEvidence,
    EvidenceAggregate,
)
from .explainability import (
    DecisionTrace,
    ExplainabilityBuilder,
)
from .governance import (
    EvidenceGovernanceEngine,
    EvidenceGovernanceResult,
)


@dataclass(frozen=True)
class DecisionPolicy:
    buy_direction_threshold: float = 0.60
    sell_direction_threshold: float = 0.60
    minimum_confidence: float = 0.35
    maximum_conflict_ratio: float = 0.65
    minimum_usable_evidence: int = 1
    minimum_independent_clusters: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            (
                "buy_direction_threshold",
                self.buy_direction_threshold,
            ),
            (
                "sell_direction_threshold",
                self.sell_direction_threshold,
            ),
            (
                "minimum_confidence",
                self.minimum_confidence,
            ),
            (
                "maximum_conflict_ratio",
                self.maximum_conflict_ratio,
            ),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{name} must be between 0 and 1"
                )

        if self.minimum_usable_evidence < 1:
            raise ValueError(
                "minimum_usable_evidence must be >= 1"
            )

        if self.minimum_independent_clusters < 1:
            raise ValueError(
                "minimum_independent_clusters must be >= 1"
            )


class DecisionEngine:
    """
    LIDOMA deterministic Decision Engine.

    Preserved paths:
    - decide(): Phase 6 legacy score path
    - decide_from_evidence(): Phase 6.1 aggregation path
    - decide_from_consensus_evidence(): Phase 6.2 consensus path

    Phase 6.3.2 path:
    - decide_from_governed_evidence(): freshness-governed consensus path

    Explicit non-responsibilities:
    - no broker/exchange calls
    - no order creation
    - no portfolio mutation
    - no position sizing
    - no final risk approval
    - no direct dependency on named experts
    - no direct dependency on named AI providers
    - no direct dependency on websites or strategies
    """

    def __init__(
        self,
        *,
        policy: DecisionPolicy | None = None,
        aggregator: EvidenceAggregator | None = None,
        explainability: ExplainabilityBuilder | None = None,
        consensus_engine: ConsensusEngine | None = None,
        governance_engine: EvidenceGovernanceEngine | None = None,
    ) -> None:
        self.policy = policy or DecisionPolicy()
        self.aggregator = (
            aggregator
            or EvidenceAggregator()
        )
        self.explainability = (
            explainability
            or ExplainabilityBuilder()
        )
        self.consensus_engine = (
            consensus_engine
            or ConsensusEngine()
        )
        self.governance_engine = (
            governance_engine
            or EvidenceGovernanceEngine()
        )

    def decide(
        self,
        context: DecisionContext,
        score: DecisionScore,
    ) -> Decision:
        """
        Backward-compatible Phase 6 foundation path.
        """
        final = score.final_score()

        if final >= 0.75:
            action = DecisionAction.BUY
        elif final <= 0.35:
            action = DecisionAction.SELL
        else:
            action = DecisionAction.HOLD

        return Decision.create(
            action=action,
            confidence=final,
            reasoning=(
                *context.signals,
                "generated_by_legacy_score_path",
            ),
        )

    def decide_from_evidence(
        self,
        context: DecisionContext,
        evidence: tuple[DecisionEvidence, ...],
    ) -> tuple[Decision, DecisionTrace]:
        """
        Preserved Phase 6.1 deterministic evidence path.
        """
        aggregate = self.aggregator.aggregate(
            evidence
        )

        trace = self.explainability.build(
            context=context,
            evidence=evidence,
            aggregate=aggregate,
        )

        action, reason = self._select_action(
            aggregate
        )

        decision = Decision.create(
            action=action,
            confidence=aggregate.confidence,
            reasoning=(
                reason,
                *trace.summary,
            ),
            evidence_ids=aggregate.evidence_ids,
            conflict_ratio=aggregate.conflict_ratio,
        )

        return decision, trace

    def decide_from_consensus_evidence(
        self,
        context: DecisionContext,
        evidence: tuple[DecisionEvidence, ...],
    ) -> tuple[
        Decision,
        DecisionTrace,
        ConsensusResult,
    ]:
        """
        Preserved Phase 6.2 correlation/reliability-aware path.
        """
        consensus = self.consensus_engine.evaluate(
            evidence
        )

        trace = self.explainability.build(
            context=context,
            evidence=evidence,
            aggregate=consensus.aggregate,
        )

        action, reason = (
            self._select_consensus_action(
                consensus
            )
        )

        decision = Decision.create(
            action=action,
            confidence=consensus.aggregate.confidence,
            reasoning=(
                f"phase_6_2_consensus:{reason}",
                (
                    "independent_clusters="
                    f"{consensus.independent_cluster_count}"
                ),
                (
                    "usable_clusters="
                    f"{consensus.usable_cluster_count}"
                ),
                (
                    "correlated_clusters="
                    f"{consensus.correlated_cluster_count}"
                ),
                (
                    "duplication_discount_ratio="
                    f"{consensus.duplication_discount_ratio:.6f}"
                ),
                *trace.summary,
            ),
            evidence_ids=consensus.aggregate.evidence_ids,
            conflict_ratio=consensus.aggregate.conflict_ratio,
            consensus_score=consensus.aggregate.agreement_ratio,
            independent_cluster_count=(
                consensus.independent_cluster_count
            ),
        )

        return decision, trace, consensus

    def decide_from_governed_evidence(
        self,
        context: DecisionContext,
        evidence: tuple[DecisionEvidence, ...],
        *,
        evaluated_at: datetime | None = None,
    ) -> tuple[
        Decision,
        DecisionTrace,
        ConsensusResult,
        EvidenceGovernanceResult,
    ]:
        """
        Phase 6.3.2 governance-aware consensus path.

        Evidence is evaluated for freshness before consensus.

        Rejected evidence:
        - remains in EvidenceGovernanceResult for audit
        - does not participate in clustering
        - does not participate in reliability weighting
        - cannot affect consensus

        Stale accepted evidence receives deterministic freshness decay.

        The resulting Decision remains only a proposal and cannot bypass the
        future Risk Engine.
        """
        governance = self.governance_engine.evaluate(
            evidence,
            evaluated_at=evaluated_at,
        )

        governed_all = (
            governance.accepted
            + governance.rejected
        )

        consensus = (
            self.consensus_engine.evaluate_governed(
                governed_all
            )
        )

        accepted_evidence = (
            governance.accepted_evidence
        )

        trace = self.explainability.build(
            context=context,
            evidence=accepted_evidence,
            aggregate=consensus.aggregate,
        )

        action, reason = (
            self._select_consensus_action(
                consensus
            )
        )

        decision = Decision.create(
            action=action,
            confidence=consensus.aggregate.confidence,
            reasoning=(
                f"phase_6_3_2_governance:{reason}",
                (
                    "governance_evaluated="
                    f"{governance.evaluated_count}"
                ),
                (
                    "governance_accepted="
                    f"{governance.accepted_count}"
                ),
                (
                    "governance_rejected="
                    f"{governance.rejected_count}"
                ),
                (
                    "independent_clusters="
                    f"{consensus.independent_cluster_count}"
                ),
                (
                    "usable_clusters="
                    f"{consensus.usable_cluster_count}"
                ),
                (
                    "correlated_clusters="
                    f"{consensus.correlated_cluster_count}"
                ),
                (
                    "duplication_discount_ratio="
                    f"{consensus.duplication_discount_ratio:.6f}"
                ),
                *trace.summary,
            ),
            evidence_ids=consensus.aggregate.evidence_ids,
            conflict_ratio=consensus.aggregate.conflict_ratio,
            consensus_score=consensus.aggregate.agreement_ratio,
            independent_cluster_count=(
                consensus.independent_cluster_count
            ),
        )

        return (
            decision,
            trace,
            consensus,
            governance,
        )

    def _select_consensus_action(
        self,
        consensus: ConsensusResult,
    ) -> tuple[DecisionAction, str]:
        """
        Apply the independent usable cluster gate before general policy.
        """
        if (
            consensus.usable_cluster_count
            < self.policy.minimum_independent_clusters
        ):
            return (
                DecisionAction.NO_TRADE,
                "no_trade:"
                "insufficient_independent_evidence_clusters",
            )

        return self._select_action(
            consensus.aggregate
        )

    def _select_action(
        self,
        aggregate: EvidenceAggregate,
    ) -> tuple[DecisionAction, str]:
        if (
            aggregate.usable_evidence_count
            < self.policy.minimum_usable_evidence
        ):
            return (
                DecisionAction.NO_TRADE,
                "no_trade:insufficient_usable_evidence",
            )

        if (
            aggregate.conflict_ratio
            > self.policy.maximum_conflict_ratio
        ):
            return (
                DecisionAction.NO_TRADE,
                "no_trade:"
                "evidence_conflict_above_policy_limit",
            )

        if (
            aggregate.confidence
            < self.policy.minimum_confidence
        ):
            return (
                DecisionAction.NO_TRADE,
                "no_trade:confidence_below_policy_minimum",
            )

        if (
            aggregate.direction_score
            >= self.policy.buy_direction_threshold
        ):
            return (
                DecisionAction.BUY,
                "buy:"
                "bullish_evidence_exceeds_policy_threshold",
            )

        if (
            aggregate.direction_score
            <= -self.policy.sell_direction_threshold
        ):
            return (
                DecisionAction.SELL,
                "sell:"
                "bearish_evidence_exceeds_policy_threshold",
            )

        return (
            DecisionAction.HOLD,
            "hold:"
            "directional_evidence_below_trade_threshold",
        )