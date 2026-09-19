from datetime import datetime, timezone

import pytest

from lidoma_engines.decision import (
    DecisionOutcome,
    DecisionOutcomeStatus,
)


NOW = datetime.now(timezone.utc)


def test_create_success_outcome():

    outcome = DecisionOutcome(
        decision_id="decision-001",
        status=DecisionOutcomeStatus.SUCCESS,
        evaluated_at=NOW,
        realized_return=0.05,
        reason="target_reached",
    )

    assert outcome.decision_id == "decision-001"
    assert outcome.status == DecisionOutcomeStatus.SUCCESS
    assert outcome.realized_return == 0.05


def test_reject_empty_decision_id():

    with pytest.raises(ValueError):

        DecisionOutcome(
            decision_id="",
            status=DecisionOutcomeStatus.SUCCESS,
            evaluated_at=NOW,
        )


def test_reject_naive_datetime():

    with pytest.raises(ValueError):

        DecisionOutcome(
            decision_id="decision-001",
            status=DecisionOutcomeStatus.SUCCESS,
            evaluated_at=datetime.now(),
        )