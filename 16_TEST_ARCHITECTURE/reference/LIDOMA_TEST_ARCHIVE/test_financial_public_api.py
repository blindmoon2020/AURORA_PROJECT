from lidoma_finance import (
    MarketData,
    StrategyDefinition,
    SimulationResult,
    TradeOrder,
    Portfolio,
    FinancialRiskAssessment,
    RiskGate,
    TradingAgent,
    BrokerConnection,
    FinancialDecisionContext,
    FinancialDecision,
    FinancialDecisionEngine,
    TradingWorkflow,
    FinancialExperienceRecord,
    EvolutionFeedback,
    LearningCycle,
)


def test_financial_public_api():

    assert MarketData
    assert StrategyDefinition
    assert SimulationResult
    assert TradeOrder
    assert Portfolio
    assert FinancialRiskAssessment
    assert RiskGate
    assert TradingAgent
    assert BrokerConnection
    assert FinancialDecisionContext
    assert FinancialDecision
    assert FinancialDecisionEngine
    assert TradingWorkflow
    assert FinancialExperienceRecord
    assert EvolutionFeedback
    assert LearningCycle