from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from lidoma_engines.decision.consensus import (
    ConsensusEngine,
)
from lidoma_engines.decision.decision import (
    DecisionAction,
)
from lidoma_engines.decision.decision_context import (
    DecisionContext,
)
from lidoma_engines.decision.decision_engine import (
    DecisionEngine,
)
from lidoma_engines.decision.evidence import (
    DecisionEvidence,
    EvidenceDirection,
    EvidenceQuality,
)
from lidoma_engines.decision.freshness import (
    EvidenceFreshnessEvaluator,
    EvidenceFreshnessPolicy,
    FreshnessStatus,
)
from lidoma_engines.decision.freshness_decay import (
    FreshnessDecayEvaluator,
)
from lidoma_engines.decision.governance import (
    EvidenceGovernanceDisposition,
    EvidenceGovernanceEngine,
)


NOW = datetime(
    2026,
    9,
    9,
    18,
    0,
    tzinfo=timezone.utc,
)


POLICY = EvidenceFreshnessPolicy(
    default_stale_after=timedelta(hours=1),
    default_expire_after=timedelta(hours=3),
    maximum_future_skew=timedelta(seconds=30),
)


def governance_engine() -> EvidenceGovernanceEngine:
    return EvidenceGovernanceEngine(
        freshness_evaluator=EvidenceFreshnessEvaluator(
            POLICY
        )
    )


def make_evidence(
    *,
    evidence_id: str,
    source_id: str,
    direction: EvidenceDirection,
    created_at: datetime,
    capability: str = "technical.structure",
    confidence: float = 1.0,
    reliability: float = 1.0,
    weight: float = 1.0,
    dependency_keys: tuple[str, ...] = (),
) -> DecisionEvidence:
    return DecisionEvidence(
        source_id=source_id,
        capability=capability,
        direction=direction,
        quality=EvidenceQuality(
            confidence=confidence,
            reliability=reliability,
            weight=weight,
        ),
        reason=f"test evidence {evidence_id}",
        evidence_id=evidence_id,
        created_at=created_at,
        dependency_keys=dependency_keys,
    )


def test_fresh_decay_factor_is_one() -> None:
    evidence = make_evidence(
        evidence_id="fresh",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=30),
    )

    governed = governance_engine().evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert governed.freshness.status == FreshnessStatus.FRESH
    assert governed.freshness_factor == pytest.approx(1.0)
    assert governed.disposition == (
        EvidenceGovernanceDisposition.ACCEPT
    )


def test_stale_midpoint_decay_factor_is_half() -> None:
    evidence = make_evidence(
        evidence_id="stale-midpoint",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(hours=2),
    )

    governed = governance_engine().evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert governed.freshness.status == FreshnessStatus.STALE
    assert governed.freshness_factor == pytest.approx(0.5)
    assert governed.disposition == (
        EvidenceGovernanceDisposition.ACCEPT_WITH_WARNING
    )


def test_expired_evidence_has_zero_factor_and_is_rejected() -> None:
    evidence = make_evidence(
        evidence_id="expired",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(hours=4),
    )

    governed = governance_engine().evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert governed.freshness.status == FreshnessStatus.EXPIRED
    assert governed.freshness_factor == 0.0
    assert governed.is_rejected


def test_future_dated_evidence_has_zero_factor_and_is_rejected() -> None:
    evidence = make_evidence(
        evidence_id="future",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW + timedelta(minutes=5),
    )

    governed = governance_engine().evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert governed.freshness.status == (
        FreshnessStatus.FUTURE_DATED
    )
    assert governed.freshness_factor == 0.0
    assert governed.is_rejected


def test_stale_weight_is_reduced_before_consensus() -> None:
    fresh = make_evidence(
        evidence_id="fresh",
        source_id="fresh.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=30),
    )

    stale = make_evidence(
        evidence_id="stale",
        source_id="stale.source",
        direction=EvidenceDirection.BEARISH,
        created_at=NOW - timedelta(hours=2),
    )

    governance = governance_engine().evaluate(
        (fresh, stale),
        evaluated_at=NOW,
    )

    consensus = ConsensusEngine().evaluate_governed(
        governance.accepted
    )

    assert consensus.aggregate.bullish_weight == pytest.approx(
        1.0
    )
    assert consensus.aggregate.bearish_weight == pytest.approx(
        0.5
    )
    assert consensus.raw_effective_weight == pytest.approx(
        1.5
    )


def test_rejected_evidence_cannot_influence_consensus() -> None:
    fresh = make_evidence(
        evidence_id="fresh",
        source_id="fresh.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=10),
    )

    expired = make_evidence(
        evidence_id="expired",
        source_id="expired.source",
        direction=EvidenceDirection.BEARISH,
        created_at=NOW - timedelta(hours=5),
    )

    governance = governance_engine().evaluate(
        (fresh, expired),
        evaluated_at=NOW,
    )

    all_governed = (
        governance.accepted
        + governance.rejected
    )

    consensus = ConsensusEngine().evaluate_governed(
        all_governed
    )

    assert governance.rejected_count == 1
    assert consensus.aggregate.evidence_ids == (
        "fresh",
    )
    assert consensus.aggregate.bullish_weight == pytest.approx(
        1.0
    )
    assert consensus.aggregate.bearish_weight == pytest.approx(
        0.0
    )


def test_decay_is_applied_before_correlation_cap() -> None:
    fresh = make_evidence(
        evidence_id="correlated-fresh",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=10),
        dependency_keys=("shared.market.data",),
    )

    stale = make_evidence(
        evidence_id="correlated-stale",
        source_id="source.b",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(hours=2),
        dependency_keys=("shared.market.data",),
    )

    governance = governance_engine().evaluate(
        (fresh, stale),
        evaluated_at=NOW,
    )

    consensus = ConsensusEngine().evaluate_governed(
        governance.accepted
    )

    assert consensus.raw_effective_weight == pytest.approx(
        1.5
    )
    assert consensus.adjusted_effective_weight == pytest.approx(
        1.0
    )
    assert consensus.correlated_cluster_count == 1


def test_all_rejected_evidence_produces_empty_consensus() -> None:
    expired = make_evidence(
        evidence_id="expired",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(hours=5),
    )

    governance = governance_engine().evaluate(
        (expired,),
        evaluated_at=NOW,
    )

    consensus = ConsensusEngine().evaluate_governed(
        governance.rejected
    )

    assert consensus.aggregate.total_evidence_count == 0
    assert consensus.aggregate.usable_evidence_count == 0
    assert consensus.usable_cluster_count == 0
    assert consensus.raw_effective_weight == 0.0


def test_phase_6_2_evaluate_preserves_full_weight() -> None:
    old_but_legacy = make_evidence(
        evidence_id="legacy",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(days=100),
    )

    consensus = ConsensusEngine().evaluate(
        (old_but_legacy,)
    )

    assert consensus.raw_effective_weight == pytest.approx(
        1.0
    )
    assert consensus.aggregate.bullish_weight == pytest.approx(
        1.0
    )


def test_duplicate_evidence_ids_are_rejected_before_governance() -> None:
    first = make_evidence(
        evidence_id="duplicate",
        source_id="source.a",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW,
    )

    second = make_evidence(
        evidence_id="duplicate",
        source_id="source.b",
        direction=EvidenceDirection.BEARISH,
        created_at=NOW,
    )

    with pytest.raises(
        ValueError,
        match="evidence IDs must be unique",
    ):
        governance_engine().evaluate(
            (first, second),
            evaluated_at=NOW,
        )


def test_multi_asset_governance_remains_asset_agnostic() -> None:
    eurusd = make_evidence(
        evidence_id="EURUSD",
        source_id="forex.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=10),
    )

    xauusd = make_evidence(
        evidence_id="XAUUSD",
        source_id="commodity.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=20),
    )

    msft = make_evidence(
        evidence_id="MSFT",
        source_id="equity.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=30),
        capability="fundamental.earnings",
    )

    result = governance_engine().evaluate(
        (eurusd, xauusd, msft),
        evaluated_at=NOW,
    )

    assert result.accepted_count == 3
    assert result.rejected_count == 0


def test_decision_engine_governed_path_rejects_expired_opposition() -> None:
    fresh_bullish = make_evidence(
        evidence_id="fresh-bullish",
        source_id="fresh.source",
        direction=EvidenceDirection.BULLISH,
        created_at=NOW - timedelta(minutes=10),
    )

    expired_bearish = make_evidence(
        evidence_id="expired-bearish",
        source_id="expired.source",
        direction=EvidenceDirection.BEARISH,
        created_at=NOW - timedelta(hours=5),
    )

    engine = DecisionEngine(
        governance_engine=governance_engine()
    )

    context = DecisionContext(
        market="forex",
        timeframe="H1",
        signals=("governance_test",),
        asset_class="forex",
        instrument="EURUSD",
    )

    decision, _, consensus, governance = (
        engine.decide_from_governed_evidence(
            context,
            (
                fresh_bullish,
                expired_bearish,
            ),
            evaluated_at=NOW,
        )
    )

    assert governance.accepted_count == 1
    assert governance.rejected_count == 1
    assert consensus.aggregate.evidence_ids == (
        "fresh-bullish",
    )
    assert decision.action == DecisionAction.BUY
