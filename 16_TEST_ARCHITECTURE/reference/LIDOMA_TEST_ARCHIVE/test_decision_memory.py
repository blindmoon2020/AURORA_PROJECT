from datetime import datetime, timezone

from lidoma_engines.decision import (
    Decision,
    DecisionAction,
    DecisionMemoryRecord,
    InMemoryDecisionMemoryStore,
    DecisionOutcome,
    DecisionOutcomeStatus,
)


NOW = datetime.now(timezone.utc)


def create_test_decision():

    return Decision.create(
        action=DecisionAction.BUY,
        confidence=0.85,
        reasoning=(
            "memory_test",
        ),
        evidence_ids=(
            "evidence-001",
        ),
        consensus_score=0.8,
        independent_cluster_count=2,
    )


def test_save_and_get_memory_record():

    decision = create_test_decision()

    record = DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
    )

    store = InMemoryDecisionMemoryStore()

    store.save(record)

    result = store.get(
        decision.decision_id
    )

    assert result is not None
    assert result.decision.decision_id == (
        decision.decision_id
    )


def test_memory_record_with_outcome():

    decision = create_test_decision()

    outcome = DecisionOutcome(
        decision_id=decision.decision_id,
        status=DecisionOutcomeStatus.SUCCESS,
        evaluated_at=NOW,
        realized_return=0.04,
    )

    record = DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
        outcome=outcome,
    )

    store = InMemoryDecisionMemoryStore()

    store.save(record)

    result = store.get(
        decision.decision_id
    )

    assert result is not None
    assert result.outcome is not None
    assert result.outcome.status == (
        DecisionOutcomeStatus.SUCCESS
    )


def test_all_returns_saved_records():

    decision = create_test_decision()

    record = DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
    )

    store = InMemoryDecisionMemoryStore()

    store.save(record)

    records = store.all()

    assert len(records) == 1
    assert (
        records[0].decision.decision_id
        ==
        decision.decision_id
    )