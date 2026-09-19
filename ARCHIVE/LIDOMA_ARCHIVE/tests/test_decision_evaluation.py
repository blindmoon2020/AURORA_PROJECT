from datetime import datetime, timezone

from lidoma_engines.decision import (
    Decision,
    DecisionAction,
    DecisionEvaluator,
    DecisionMemoryRecord,
    DecisionOutcome,
    DecisionOutcomeStatus,
)


NOW = datetime.now(timezone.utc)


def create_decision():

    return Decision.create(
        action=DecisionAction.BUY,
        confidence=0.9,
        reasoning=(
            "evaluation_test",
        ),
    )


def test_evaluator_calculates_success_rate():

    decision_one = create_decision()
    decision_two = create_decision()

    success = DecisionOutcome(
        decision_id=decision_one.decision_id,
        status=DecisionOutcomeStatus.SUCCESS,
        evaluated_at=NOW,
        realized_return=0.03,
    )

    failure = DecisionOutcome(
        decision_id=decision_two.decision_id,
        status=DecisionOutcomeStatus.FAILURE,
        evaluated_at=NOW,
        realized_return=-0.02,
    )

    records = (
        DecisionMemoryRecord(
            decision=decision_one,
            created_at=NOW,
            outcome=success,
        ),
        DecisionMemoryRecord(
            decision=decision_two,
            created_at=NOW,
            outcome=failure,
        ),
    )

    result = DecisionEvaluator().evaluate(records)

    assert result.total_evaluated == 2
    assert result.successful == 1
    assert result.failed == 1
    assert result.accuracy == 0.5


def test_unknown_outcome_is_not_counted():

    decision = create_decision()

    unknown = DecisionOutcome(
        decision_id=decision.decision_id,
        status=DecisionOutcomeStatus.UNKNOWN,
        evaluated_at=NOW,
    )

    record = DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
        outcome=unknown,
    )

    result = DecisionEvaluator().evaluate(
        (record,)
    )

    assert result.total_evaluated == 0
    assert result.accuracy == 0.0


def test_empty_records():

    result = DecisionEvaluator().evaluate(
        ()
    )

    assert result.total_evaluated == 0
    assert result.successful == 0
    assert result.failed == 0