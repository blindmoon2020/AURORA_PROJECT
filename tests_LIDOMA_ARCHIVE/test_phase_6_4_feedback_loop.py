from datetime import datetime, timezone

from lidoma_engines.decision import (
    Decision,
    DecisionAction,
    DecisionMemoryRecord,
    InMemoryDecisionMemoryStore,
    DecisionOutcome,
    DecisionOutcomeStatus,
    DecisionIntelligenceEngine,
    FeedbackDecision,
    FeedbackReview,
    FeedbackGovernanceEngine,
)


NOW = datetime.now(timezone.utc)


def test_complete_feedback_loop():

    decision = Decision.create(
        action=DecisionAction.BUY,
        confidence=0.85,
        reasoning=(
            "feedback_loop_test",
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

    proposal = (
        DecisionIntelligenceEngine()
        .build_source_proposal(
            "source.alpha",
            store.all(),
        )
    )

    review = FeedbackReview(
        proposal=proposal,
        decision=FeedbackDecision.APPROVED,
        reviewer="policy_engine",
        reason="approved_feedback",
    )

    result = (
        FeedbackGovernanceEngine()
        .review(review)
    )

    assert proposal.success_rate == 1.0
    assert proposal.proposed_adjustment == 0.5

    assert result.approved is True
    assert result.adjustment == 0.5
    assert result.source_id == "source.alpha"