from datetime import datetime, timezone

import pytest

from lidoma_engines.decision import (
    DecisionAction,
    DecisionContext,
    DecisionEngine,
    DecisionEvidence,
    DecisionPolicy,
    EvidenceAggregator,
    EvidenceDirection,
    EvidenceQuality,
)
from lidoma_engines.provenance import ProvenanceRecord


def evidence(
    source_id,
    capability,
    direction,
    confidence,
    reason,
    *,
    reliability=1.0,
    weight=1.0,
    provenance=None,
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
        provenance=provenance,
    )


def test_aggregator_is_provider_agnostic_and_multi_asset_safe():
    items = (
        evidence(
            "expert.example_one",
            "price_action",
            EvidenceDirection.BULLISH,
            0.90,
            "higher-high structure",
        ),
        evidence(
            "ai.provider_example",
            "fundamental_analysis",
            EvidenceDirection.BULLISH,
            0.80,
            "earnings evidence supports thesis",
        ),
        evidence(
            "source.market_example",
            "support_resistance",
            EvidenceDirection.NEUTRAL,
            0.50,
            "price near resistance",
        ),
    )

    aggregate = EvidenceAggregator().aggregate(items)

    assert aggregate.bullish_weight > 0
    assert aggregate.neutral_weight > 0
    assert aggregate.direction_score == pytest.approx(1.0)
    assert aggregate.total_evidence_count == 3
    assert set(aggregate.source_ids) == {
        "expert.example_one",
        "ai.provider_example",
        "source.market_example",
    }


def test_equal_opposing_evidence_detects_maximum_conflict():
    items = (
        evidence(
            "analysis.one",
            "price_action",
            EvidenceDirection.BULLISH,
            1.0,
            "bullish structure",
        ),
        evidence(
            "analysis.two",
            "price_action",
            EvidenceDirection.BEARISH,
            1.0,
            "bearish rejection",
        ),
    )

    aggregate = EvidenceAggregator().aggregate(items)

    assert aggregate.direction_score == pytest.approx(0.0)
    assert aggregate.conflict_ratio == pytest.approx(1.0)
    assert aggregate.confidence == pytest.approx(0.0)


def test_decision_engine_returns_no_trade_when_evidence_conflicts():
    engine = DecisionEngine()

    decision, trace = engine.decide_from_evidence(
        DecisionContext(
            market="forex",
            timeframe="1H",
            asset_class="forex",
            instrument="EURUSD",
        ),
        (
            evidence(
                "expert.alpha",
                "price_action",
                EvidenceDirection.BULLISH,
                1.0,
                "bullish break",
            ),
            evidence(
                "expert.beta",
                "macro",
                EvidenceDirection.BEARISH,
                1.0,
                "bearish macro evidence",
            ),
        ),
    )

    assert decision.action == DecisionAction.NO_TRADE
    assert decision.conflict_ratio == pytest.approx(1.0)
    assert trace.conflict_ratio == pytest.approx(1.0)
    assert decision.evidence_ids == trace.evidence_ids


def test_decision_engine_can_issue_buy_for_convergent_evidence():
    engine = DecisionEngine(
        policy=DecisionPolicy(
            buy_direction_threshold=0.60,
            sell_direction_threshold=0.60,
            minimum_confidence=0.30,
            maximum_conflict_ratio=0.65,
            minimum_usable_evidence=2,
        )
    )

    decision, trace = engine.decide_from_evidence(
        DecisionContext(
            market="commodities",
            timeframe="4H",
            asset_class="commodity",
            instrument="XAUUSD",
        ),
        (
            evidence(
                "analysis.price_action",
                "price_action",
                EvidenceDirection.BULLISH,
                0.90,
                "bullish displacement",
            ),
            evidence(
                "analysis.fibonacci",
                "fibonacci",
                EvidenceDirection.BULLISH,
                0.80,
                "retracement confluence",
            ),
        ),
    )

    assert decision.action == DecisionAction.BUY
    assert decision.confidence >= 0.30
    assert "analysis.price_action" in trace.source_ids
    assert "analysis.fibonacci" in trace.source_ids


def test_zero_weight_evidence_is_not_usable():
    aggregate = EvidenceAggregator().aggregate(
        (
            evidence(
                "source.zero",
                "sentiment",
                EvidenceDirection.BULLISH,
                1.0,
                "ignored by policy weight",
                weight=0.0,
            ),
        )
    )

    assert aggregate.usable_evidence_count == 0
    assert aggregate.confidence == 0.0


def test_quality_validation_rejects_invalid_values():
    with pytest.raises(ValueError):
        EvidenceQuality(confidence=1.01)

    with pytest.raises(ValueError):
        EvidenceQuality(confidence=0.8, reliability=-0.01)


def test_provenance_is_preserved_on_decision_evidence():
    provenance = ProvenanceRecord(
        source_id="source.example",
        source_type="market_source",
        captured_at=datetime.now(timezone.utc),
        source_reference="example://observation/123",
        confidence=0.9,
    )

    item = evidence(
        "source.example",
        "support_resistance",
        EvidenceDirection.BEARISH,
        0.8,
        "rejection from resistance",
        provenance=provenance,
    )

    assert item.provenance is provenance


def test_explainability_trace_contains_request_and_evidence_sources():
    context = DecisionContext(
        market="equities",
        timeframe="1D",
        asset_class="equity",
        instrument="MSFT",
    )

    decision, trace = DecisionEngine().decide_from_evidence(
        context,
        (
            evidence(
                "expert.dynamic_registry_member",
                "fundamental_analysis",
                EvidenceDirection.BULLISH,
                0.85,
                "valuation evidence supports thesis",
            ),
        ),
    )

    assert trace.request_id == context.request_id
    assert "expert.dynamic_registry_member" in trace.source_ids
    assert any(
        "expert.dynamic_registry_member" in line
        for line in trace.summary
    )
    assert decision.evidence_ids == trace.evidence_ids
