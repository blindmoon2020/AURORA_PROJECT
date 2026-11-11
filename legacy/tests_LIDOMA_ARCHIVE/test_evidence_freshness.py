from datetime import datetime, timedelta, timezone

import pytest

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


def make_evidence(
    *,
    evidence_id: str,
    created_at: datetime,
    capability: str = "technical.structure",
) -> DecisionEvidence:
    return DecisionEvidence(
        source_id="test.source",
        capability=capability,
        direction=EvidenceDirection.BULLISH,
        quality=EvidenceQuality(
            confidence=0.8,
            reliability=0.9,
            weight=1.0,
        ),
        reason="deterministic test evidence",
        evidence_id=evidence_id,
        created_at=created_at,
    )


def test_fresh_evidence_is_classified_as_fresh() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(minutes=30),
            default_expire_after=timedelta(hours=2),
        )
    )

    evidence = make_evidence(
        evidence_id="fresh-1",
        created_at=NOW - timedelta(minutes=10),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.FRESH
    assert result.is_fresh
    assert result.is_usable
    assert result.age == timedelta(minutes=10)


def test_stale_evidence_remains_usable() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(minutes=30),
            default_expire_after=timedelta(hours=2),
        )
    )

    evidence = make_evidence(
        evidence_id="stale-1",
        created_at=NOW - timedelta(minutes=45),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.STALE
    assert not result.is_fresh
    assert result.is_usable


def test_expired_evidence_is_not_usable() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(minutes=30),
            default_expire_after=timedelta(hours=2),
        )
    )

    evidence = make_evidence(
        evidence_id="expired-1",
        created_at=NOW - timedelta(hours=3),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.EXPIRED
    assert not result.is_usable


def test_future_dated_evidence_beyond_skew_is_rejected() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            maximum_future_skew=timedelta(seconds=30),
        )
    )

    evidence = make_evidence(
        evidence_id="future-1",
        created_at=NOW + timedelta(minutes=5),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.FUTURE_DATED
    assert not result.is_usable


def test_small_clock_skew_is_treated_as_zero_age() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            maximum_future_skew=timedelta(seconds=30),
        )
    )

    evidence = make_evidence(
        evidence_id="future-within-skew",
        created_at=NOW + timedelta(seconds=10),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.FRESH
    assert result.age == timedelta(0)


def test_capability_specific_policy_overrides_default() -> None:
    evaluator = EvidenceFreshnessEvaluator(
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(hours=1),
            default_expire_after=timedelta(hours=4),
            capability_stale_after={
                "market.microstructure": timedelta(seconds=30),
            },
            capability_expire_after={
                "market.microstructure": timedelta(minutes=5),
            },
        )
    )

    evidence = make_evidence(
        evidence_id="microstructure-1",
        capability="market.microstructure",
        created_at=NOW - timedelta(minutes=2),
    )

    result = evaluator.evaluate(
        evidence,
        evaluated_at=NOW,
    )

    assert result.status == FreshnessStatus.STALE
    assert result.stale_after == timedelta(seconds=30)
    assert result.expire_after == timedelta(minutes=5)


def test_policy_rejects_expiration_before_stale_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="default_expire_after must be greater",
    ):
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(hours=2),
            default_expire_after=timedelta(hours=1),
        )


def test_policy_rejects_invalid_capability_thresholds() -> None:
    with pytest.raises(
        ValueError,
        match="expire_after must be greater",
    ):
        EvidenceFreshnessPolicy(
            default_stale_after=timedelta(minutes=30),
            default_expire_after=timedelta(hours=4),
            capability_stale_after={
                "fundamental.earnings": timedelta(hours=3),
            },
            capability_expire_after={
                "fundamental.earnings": timedelta(hours=2),
            },
        )


def test_evaluator_requires_timezone_aware_evaluation_time() -> None:
    evaluator = EvidenceFreshnessEvaluator()

    evidence = make_evidence(
        evidence_id="timezone-1",
        created_at=NOW,
    )

    with pytest.raises(
        ValueError,
        match="evaluated_at must be timezone-aware",
    ):
        evaluator.evaluate(
            evidence,
            evaluated_at=datetime(2026, 9, 9, 18, 0),
        )


def test_governance_accepts_fresh_evidence() -> None:
    engine = EvidenceGovernanceEngine(
        EvidenceFreshnessEvaluator(
            EvidenceFreshnessPolicy(
                default_stale_after=timedelta(minutes=30),
                default_expire_after=timedelta(hours=2),
            )
        )
    )

    evidence = make_evidence(
        evidence_id="governance-fresh",
        created_at=NOW - timedelta(minutes=5),
    )

    result = engine.evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert result.disposition == (
        EvidenceGovernanceDisposition.ACCEPT
    )
    assert result.is_accepted
    assert not result.is_rejected


def test_governance_accepts_stale_with_warning() -> None:
    engine = EvidenceGovernanceEngine(
        EvidenceFreshnessEvaluator(
            EvidenceFreshnessPolicy(
                default_stale_after=timedelta(minutes=30),
                default_expire_after=timedelta(hours=2),
            )
        )
    )

    evidence = make_evidence(
        evidence_id="governance-stale",
        created_at=NOW - timedelta(minutes=50),
    )

    result = engine.evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert result.disposition == (
        EvidenceGovernanceDisposition.ACCEPT_WITH_WARNING
    )
    assert result.is_accepted


def test_governance_rejects_expired_evidence() -> None:
    engine = EvidenceGovernanceEngine(
        EvidenceFreshnessEvaluator(
            EvidenceFreshnessPolicy(
                default_stale_after=timedelta(minutes=30),
                default_expire_after=timedelta(hours=2),
            )
        )
    )

    evidence = make_evidence(
        evidence_id="governance-expired",
        created_at=NOW - timedelta(hours=3),
    )

    result = engine.evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert result.disposition == (
        EvidenceGovernanceDisposition.REJECT
    )
    assert result.is_rejected


def test_governance_rejects_future_dated_evidence() -> None:
    engine = EvidenceGovernanceEngine()

    evidence = make_evidence(
        evidence_id="governance-future",
        created_at=NOW + timedelta(hours=1),
    )

    result = engine.evaluate_one(
        evidence,
        evaluated_at=NOW,
    )

    assert result.disposition == (
        EvidenceGovernanceDisposition.REJECT
    )
    assert result.is_rejected


def test_governance_preserves_input_order() -> None:
    engine = EvidenceGovernanceEngine(
        EvidenceFreshnessEvaluator(
            EvidenceFreshnessPolicy(
                default_stale_after=timedelta(minutes=30),
                default_expire_after=timedelta(hours=2),
            )
        )
    )

    first = make_evidence(
        evidence_id="first",
        created_at=NOW - timedelta(minutes=5),
    )
    second = make_evidence(
        evidence_id="second",
        created_at=NOW - timedelta(minutes=10),
    )
    third = make_evidence(
        evidence_id="third",
        created_at=NOW - timedelta(hours=5),
    )

    result = engine.evaluate(
        (first, second, third),
        evaluated_at=NOW,
    )

    assert tuple(
        item.evidence.evidence_id
        for item in result.accepted
    ) == (
        "first",
        "second",
    )

    assert tuple(
        item.evidence.evidence_id
        for item in result.rejected
    ) == (
        "third",
    )

    assert result.accepted_count == 2
    assert result.rejected_count == 1
    assert result.evaluated_count == 3


def test_multi_asset_evidence_is_not_special_cased() -> None:
    engine = EvidenceGovernanceEngine()

    eurusd = DecisionEvidence(
        source_id="forex.source",
        capability="technical.structure",
        direction=EvidenceDirection.BULLISH,
        quality=EvidenceQuality(
            confidence=0.8,
            reliability=0.9,
            weight=1.0,
        ),
        reason="EURUSD structure",
        evidence_id="eurusd",
        created_at=NOW - timedelta(minutes=5),
        tags=("EURUSD", "FOREX"),
    )

    xauusd = DecisionEvidence(
        source_id="commodity.source",
        capability="technical.structure",
        direction=EvidenceDirection.BEARISH,
        quality=EvidenceQuality(
            confidence=0.7,
            reliability=0.8,
            weight=1.0,
        ),
        reason="XAUUSD structure",
        evidence_id="xauusd",
        created_at=NOW - timedelta(minutes=5),
        tags=("XAUUSD", "COMMODITY"),
    )

    msft = DecisionEvidence(
        source_id="equity.source",
        capability="fundamental.earnings",
        direction=EvidenceDirection.NEUTRAL,
        quality=EvidenceQuality(
            confidence=0.9,
            reliability=0.95,
            weight=1.0,
        ),
        reason="MSFT earnings evidence",
        evidence_id="msft",
        created_at=NOW - timedelta(minutes=5),
        tags=("MSFT", "EQUITY"),
    )

    result = engine.evaluate(
        (eurusd, xauusd, msft),
        evaluated_at=NOW,
    )

    assert result.accepted_count == 3
    assert result.rejected_count == 0