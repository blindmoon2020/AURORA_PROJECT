from lidoma_finance import (
    MarketData,
    StrategyDefinition,
    Portfolio,
    FinancialRiskAssessment,
    TradingAgent,
)


from lidoma_architecture.governance import (
    FinancialModuleContract,
    RiskGateRule,
)


from datetime import datetime, timezone


def test_financial_module_contract():

    contract = FinancialModuleContract(
        module_name="risk",
        module_type="risk",
        version="3.0.0",
    )

    assert contract.version == "3.0.0"



def test_market_contract():

    data = MarketData(
        symbol="EURUSD",
        price=1.08,
        volume=1000,
        timeframe="H1",
        timestamp=datetime.now(timezone.utc),
    )

    assert data.symbol == "EURUSD"



def test_strategy_contract():

    strategy = StrategyDefinition(
        strategy_id="S001",
        name="ICT Strategy",
        description="Liquidity strategy",
    )

    assert strategy.name == "ICT Strategy"



def test_portfolio_contract():

    portfolio = Portfolio(
        portfolio_id="P001",
        name="Main Portfolio",
        assets={
            "BTC":0.5
        },
    )

    assert portfolio.portfolio_id == "P001"



def test_risk_gate():

    rule = RiskGateRule()

    assert rule.block_without_approval is True



def test_trading_agent():

    agent = TradingAgent(
        agent_id="A001",
        name="Trader Agent",
    )

    assert agent.name == "Trader Agent"