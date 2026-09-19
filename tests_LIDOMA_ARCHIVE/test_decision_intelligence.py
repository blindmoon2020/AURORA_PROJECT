from datetime import datetime, timezone

from lidoma_engines.decision import (
    Decision,
    DecisionAction,
    DecisionIntelligenceEngine,
    DecisionMemoryRecord,
    DecisionOutcome,
    DecisionOutcomeStatus,
)


NOW = datetime.now(timezone.utc)


def make_record(status):

    decision = Decision.create(
        action=DecisionAction.BUY,
        confidence=0.8,
        reasoning=(
            "intelligence_test",
        ),
        evidence_ids=(
            "source.alpha",
        ),
    )

    outcome = DecisionOutcome(
        decision_id=decision.decision_id,
        status=status,
        evaluated_at=NOW,
    )

    return DecisionMemoryRecord(
        decision=decision,
        created_at=NOW,
        outcome=outcome,
    )


def test_build_positive_reliability_proposal():

    engine = DecisionIntelligenceEngine()

    proposal = engine.build_source_proposal(
        "source.alpha",
        (
            make_record(
                DecisionOutcomeStatus.SUCCESS
            ),
            make_record(
                DecisionOutcomeStatus.SUCCESS
            ),
        ),
    )

    assert proposal.success_rate == 1.0
    assert proposal.proposed_adjustment == 0.5


def test_build_negative_reliability_proposal():

    engine = DecisionIntelligenceEngine()

    proposal = engine.build_source_proposal(
        "source.alpha",
        (
            make_record(
                DecisionOutcomeStatus.FAILURE
            ),
        ),
    )

    assert proposal.success_rate == 0.0
    assert proposal.proposed_adjustment == -0.5


def test_no_history_returns_zero_adjustment():

    engine = DecisionIntelligenceEngine()

    proposal = engine.build_source_proposal(
        "source.alpha",
        (),
    )

    assert proposal.evaluated_decisions == 0
    assert proposal.proposed_adjustment == 0.0