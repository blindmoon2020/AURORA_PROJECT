from lidoma_engines.decision import (
    FeedbackDecision,
    FeedbackGovernanceEngine,
    FeedbackReview,
    ReliabilityAdjustmentProposal,
)


def make_proposal():

    return ReliabilityAdjustmentProposal(
        source_id="source.alpha",
        evaluated_decisions=10,
        success_rate=0.8,
        proposed_adjustment=0.3,
        reason="historical_performance",
    )


def test_approved_feedback():

    engine = FeedbackGovernanceEngine()

    review = FeedbackReview(
        proposal=make_proposal(),
        decision=FeedbackDecision.APPROVED,
        reviewer="human",
        reason="approved_after_review",
    )

    result = engine.review(review)

    assert result.approved is True
    assert result.adjustment == 0.3


def test_rejected_feedback():

    engine = FeedbackGovernanceEngine()

    review = FeedbackReview(
        proposal=make_proposal(),
        decision=FeedbackDecision.REJECTED,
        reviewer="human",
        reason="insufficient_confidence",
    )

    result = engine.review(review)

    assert result.approved is False
    assert result.adjustment == 0.0


def test_feedback_keeps_source():

    engine = FeedbackGovernanceEngine()

    review = FeedbackReview(
        proposal=make_proposal(),
        decision=FeedbackDecision.APPROVED,
        reviewer="policy",
        reason="accepted",
    )

    result = engine.review(review)

    assert result.source_id == "source.alpha"