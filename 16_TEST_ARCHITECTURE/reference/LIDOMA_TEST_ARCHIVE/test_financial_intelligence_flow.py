from datetime import datetime, timezone


from lidoma_finance import (
    FinancialDecisionContext,
    FinancialDecisionEngine,
    FinancialRiskAssessment,
    RiskGate,
    TradingWorkflow,
    FinancialExperienceRecord,
    EvolutionFeedback,
    LearningCycle,
)


def test_financial_intelligence_full_flow():

    context = FinancialDecisionContext(
        context_id="CTX001",
        symbol="BTCUSDT",
        market_state={
            "trend": "up"
        },
    )


    decision_engine = FinancialDecisionEngine()

    risk_gate = RiskGate()


    workflow = TradingWorkflow(
        decision_engine=decision_engine,
        risk_gate=risk_gate,
    )


    risk = FinancialRiskAssessment(
        assessment_id="RISK001",
        portfolio_id="PORT001",
        risk_score=0.3,
        approved=True,
    )


    approval = workflow.evaluate(
        context,
        risk,
    )


    assert approval.approved is True


    experience = FinancialExperienceRecord(
        experience_id="EXP001",
        decision_id=approval.decision_id,
        outcome="SUCCESS",
    )


    feedback = EvolutionFeedback(
        feedback_id="FB001",
        experience_id=experience.experience_id,
        improvement_signal="OPTIMIZE",
        metrics={
            "accuracy":0.8
        },
        created_at=datetime.now(timezone.utc),
    )


    learning = LearningCycle(
        cycle_id="LC001",
        strategy_id="STR001",
        experience_count=1,
        improvement_score=0.8,
        created_at=datetime.now(timezone.utc),
    )


    assert feedback.experience_id == "EXP001"
    assert learning.improvement_score == 0.8