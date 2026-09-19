from datetime import datetime, timezone

from lidoma_engines.decision import (
    Decision,
    DecisionAction,
    DecisionMemoryRecord,
    InMemoryDecisionMemoryStore,
    DecisionOutcome,
    DecisionOutcomeStatus,
    DecisionEvaluator,
    DecisionIntelligenceEngine,
)


NOW = datetime.now(timezone.utc)


def test_full_decision_lifecycle():

    decision = Decision.create(
        action=DecisionAction.BUY,
        confidence=0.85,
        reasoning=(
            "phase_6_4_integration",
        ),
        evidence_ids=(
            "source.alpha",
        ),
    )

    outcome = DecisionOutcome(
        decision_id=decision.decision_id,
        status=DecisionOutcomeStatus.SUCCESS,
        evaluated_at=NOW,
        realized_return=0.05,
    )

    record = DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
        outcome=outcome,
    )

    store = InMemoryDecisionMemoryStore()

    store.save(record)

    records = store.all()

    performance = DecisionEvaluator().evaluate(
        records
    )

    proposal = DecisionIntelligenceEngine().build_source_proposal(
        "source.alpha",
        records,
    )

    assert len(records) == 1

    assert performance.total_evaluated == 1

    assert performance.successful == 1

    assert performance.accuracy == 1.0

    assert proposal.evaluated_decisions == 1

    assert proposal.success_rate == 1.0

    assert proposal.proposed_adjustment == 0.5