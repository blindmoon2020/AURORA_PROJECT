from lidoma_engines.decision import (
    DecisionAction,
    DecisionContext,
    DecisionEngine,
    DecisionScore,
)


def test_high_confidence_decision_backward_compatibility():
    decision = DecisionEngine().decide(
        DecisionContext(
            market="crypto",
            timeframe="4H",
            signals=("liquidity sweep",),
            instrument="BTCUSDT",
        ),
        DecisionScore(0.9, 0.8, 0.85),
    )

    assert decision.action == DecisionAction.BUY


def test_explainable_decision_backward_compatibility():
    decision = DecisionEngine().decide(
        DecisionContext(
            market="equities",
            timeframe="1D",
            signals=("market structure",),
            instrument="AAPL",
        ),
        DecisionScore(0.5, 0.5, 0.5),
    )

    assert len(decision.reasoning) > 0
