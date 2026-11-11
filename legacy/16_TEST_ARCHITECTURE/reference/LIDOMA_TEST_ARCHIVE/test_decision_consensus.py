from datetime import datetime, timezone

import pytest

from lidoma_engines.decision import (
    ConsensusEngine,
    DecisionAction,
    DecisionContext,
    DecisionEngine,
    DecisionEvidence,
    DecisionPolicy,
    EvidenceCorrelationClusterer,
    EvidenceDirection,
    EvidenceQuality,
    InMemoryReliabilityResolver,
    SourceReliabilityProfile,
)


def make_evidence(
    source_id,
    capability,
    direction,
    confidence,
    reason,
    *,
    reliability=1.0,
    weight=1.0,
    dependency_keys=(),
):
    return DecisionEvidence(
        source_id=source_id,
        capability=capability,
        direction=direction,
        quality=EvidenceQuality(
            confidence=confidence,
            reliability=reliability,
            weight=weight,
        ),
        reason=reason,
        dependency_keys=dependency_keys,
    )


def test_correlated_sources_do_not_create_fake_consensus():
    evidence = (
        make_evidence(
            "ai.provider.one",
            "macro",
            EvidenceDirection.BULLISH,
            0.90,
            "same CPI event",
            dependency_keys=("macro:CPI:001",),
        ),
        make_evidence(
            "ai.provider.two",
            "macro",
            EvidenceDirection.BULLISH,
            0.90,
            "same CPI event",
            dependency_keys=("macro:CPI:001",),
        ),
        make_evidence(
            "ai.provider.three",
            "macro",
            EvidenceDirection.BULLISH,
            0.90,
            "same CPI event",
            dependency_keys=("macro:CPI:001",),
        ),
    )

    result = ConsensusEngine().evaluate(evidence)

    assert result.independent_cluster_count == 1
    assert result.usable_cluster_count == 1
    assert result.correlated_cluster_count == 1
    assert result.raw_effective_weight == pytest.approx(2.7)
    assert result.adjusted_effective_weight == pytest.approx(0.9)
    assert result.duplication_discount_ratio == pytest.approx(2 / 3)


def test_independent_analysis_sources_are_preserved():
    result = ConsensusEngine().evaluate(
        (
            make_evidence(
                "analysis.price_action",
                "price_action",
                EvidenceDirection.BULLISH,
                0.90,
                "structure breakout",
            ),
            make_evidence(
                "analysis.volume_profile",
                "fixed_range_volume_profile",
                EvidenceDirection.BULLISH,
                0.80,
                "volume confirmation",
            ),
        )
    )

    assert result.independent_cluster_count == 2
    assert result.usable_cluster_count == 2
    assert result.correlated_cluster_count == 0
    assert result.raw_effective_weight == pytest.approx(1.7)
    assert result.adjusted_effective_weight == pytest.approx(1.7)
    assert result.duplication_discount_ratio == pytest.approx(0.0)


def test_dependency_clustering_is_transitive():
    clusters = EvidenceCorrelationClusterer().cluster(
        (
            make_evidence(
                "source.a",
                "macro",
                EvidenceDirection.BULLISH,
                0.8,
                "A",
                dependency_keys=("event:x",),
            ),
            make_evidence(
                "source.b",
                "macro",
                EvidenceDirection.BULLISH,
                0.8,
                "B",
                dependency_keys=("event:x", "event:y"),
            ),
            make_evidence(
                "source.c",
                "macro",
                EvidenceDirection.BULLISH,
                0.8,
                "C",
                dependency_keys=("event:y",),
            ),
        )
    )

    assert len(clusters) == 1
    assert set(clusters[0].source_ids) == {
        "source.a",
        "source.b",
        "source.c",
    }


def test_capability_reliability_override_has_priority():
    resolver = InMemoryReliabilityResolver(
        (
            SourceReliabilityProfile(
                source_id="expert.dynamic",
                reliability_score=0.60,
            ),
            SourceReliabilityProfile(
                source_id="expert.dynamic",
                capability="fibonacci",
                reliability_score=0.90,
            ),
        )
    )

    assert resolver.resolve(
        "expert.dynamic",
        "fibonacci",
        1.0,
    ) == pytest.approx(0.90)

    assert resolver.resolve(
        "expert.dynamic",
        "macro",
        1.0,
    ) == pytest.approx(0.60)


def test_reliability_profile_rejects_naive_timestamp():
    with pytest.raises(ValueError):
        SourceReliabilityProfile(
            source_id="source.example",
            reliability_score=0.8,
            last_evaluated_at=datetime(2026, 1, 1),
        )

    profile = SourceReliabilityProfile(
        source_id="source.example",
        reliability_score=0.8,
        last_evaluated_at=datetime.now(timezone.utc),
    )

    assert profile.reliability_score == pytest.approx(0.8)


def test_consensus_engine_applies_resolved_reliability():
    resolver = InMemoryReliabilityResolver(
        (
            SourceReliabilityProfile(
                source_id="source.high",
                reliability_score=1.0,
            ),
            SourceReliabilityProfile(
                source_id="source.low",
                reliability_score=0.2,
            ),
        )
    )

    result = ConsensusEngine(
        reliability_resolver=resolver
    ).evaluate(
        (
            make_evidence(
                "source.high",
                "fundamental_analysis",
                EvidenceDirection.BULLISH,
                1.0,
                "high reliability evidence",
            ),
            make_evidence(
                "source.low",
                "fundamental_analysis",
                EvidenceDirection.BEARISH,
                1.0,
                "low reliability evidence",
            ),
        )
    )

    assert result.aggregate.direction_score > 0.0
    assert (
        result.aggregate.bullish_weight
        > result.aggregate.bearish_weight
    )


def test_conflicting_consensus_returns_no_trade():
    decision, trace, consensus = (
        DecisionEngine().decide_from_consensus_evidence(
            DecisionContext(
                market="forex",
                timeframe="1H",
                asset_class="forex",
                instrument="EURUSD",
            ),
            (
                make_evidence(
                    "analysis.price_action",
                    "price_action",
                    EvidenceDirection.BULLISH,
                    1.0,
                    "bullish structure",
                ),
                make_evidence(
                    "analysis.fundamental",
                    "fundamental_analysis",
                    EvidenceDirection.BEARISH,
                    1.0,
                    "bearish macro",
                ),
            ),
        )
    )

    assert decision.action == DecisionAction.NO_TRADE
    assert consensus.aggregate.conflict_ratio == pytest.approx(1.0)
    assert decision.evidence_ids == trace.evidence_ids


def test_duplicate_confirmation_fails_independent_cluster_policy():
    engine = DecisionEngine(
        policy=DecisionPolicy(
            minimum_independent_clusters=2
        )
    )

    decision, _, consensus = (
        engine.decide_from_consensus_evidence(
            DecisionContext(
                market="commodities",
                timeframe="15M",
                asset_class="commodity",
                instrument="XAUUSD",
            ),
            (
                make_evidence(
                    "provider.one",
                    "macro",
                    EvidenceDirection.BULLISH,
                    0.95,
                    "same upstream event",
                    dependency_keys=("event:77",),
                ),
                make_evidence(
                    "provider.two",
                    "macro",
                    EvidenceDirection.BULLISH,
                    0.95,
                    "same upstream event",
                    dependency_keys=("event:77",),
                ),
                make_evidence(
                    "provider.three",
                    "macro",
                    EvidenceDirection.BULLISH,
                    0.95,
                    "same upstream event",
                    dependency_keys=("event:77",),
                ),
            ),
        )
    )

    assert consensus.usable_cluster_count == 1
    assert decision.action == DecisionAction.NO_TRADE


def test_independent_convergent_evidence_can_buy():
    engine = DecisionEngine(
        policy=DecisionPolicy(
            minimum_independent_clusters=2
        )
    )

    decision, _, consensus = (
        engine.decide_from_consensus_evidence(
            DecisionContext(
                market="equities",
                timeframe="1D",
                asset_class="equity",
                instrument="MSFT",
            ),
            (
                make_evidence(
                    "analysis.structure",
                    "price_action",
                    EvidenceDirection.BULLISH,
                    0.90,
                    "bullish market structure",
                ),
                make_evidence(
                    "analysis.fundamental",
                    "fundamental_analysis",
                    EvidenceDirection.BULLISH,
                    0.85,
                    "independent fundamental confirmation",
                ),
            ),
        )
    )

    assert consensus.usable_cluster_count == 2
    assert decision.action == DecisionAction.BUY


def test_dependency_keys_reject_duplicates():
    with pytest.raises(ValueError):
        make_evidence(
            "source.example",
            "sentiment",
            EvidenceDirection.NEUTRAL,
            0.5,
            "duplicate key",
            dependency_keys=("dep:x", "dep:x"),
        )


def test_zero_weight_cluster_is_not_usable():
    result = ConsensusEngine().evaluate(
        (
            make_evidence(
                "source.zero",
                "sentiment",
                EvidenceDirection.BULLISH,
                0.0,
                "zero confidence",
            ),
        )
    )

    assert result.independent_cluster_count == 1
    assert result.usable_cluster_count == 0
    assert result.adjusted_effective_weight == pytest.approx(0.0)


def test_multi_asset_context_is_not_crypto_specific():
    engine = DecisionEngine(
        policy=DecisionPolicy(
            minimum_independent_clusters=2
        )
    )

    contexts = (
        DecisionContext(
            market="forex",
            timeframe="1H",
            asset_class="forex",
            instrument="EURUSD",
        ),
        DecisionContext(
            market="commodities",
            timeframe="4H",
            asset_class="commodity",
            instrument="XAUUSD",
        ),
        DecisionContext(
            market="equities",
            timeframe="1D",
            asset_class="equity",
            instrument="MSFT",
        ),
    )

    for context in contexts:
        decision, _, _ = engine.decide_from_consensus_evidence(
            context,
            (
                make_evidence(
                    "analysis.one",
                    "price_action",
                    EvidenceDirection.BULLISH,
                    0.9,
                    "technical confirmation",
                ),
                make_evidence(
                    "analysis.two",
                    "fundamental_analysis",
                    EvidenceDirection.BULLISH,
                    0.8,
                    "independent confirmation",
                ),
            ),
        )

        assert decision.action == DecisionAction.BUY
