from lidoma_engines.context import DecisionContext


def test_decision_context_creation():

    context = DecisionContext(
        decision_id="decision.context.alpha",
        market_context={
            "asset": "BTC"
        },
        portfolio_context={
            "exposure": 0.5
        },
        risk_context={
            "level": "medium"
        },
        user_context={
            "profile": "default"
        },
    )

    assert context.decision_id == (
        "decision.context.alpha"
    )

    assert context.market_context["asset"] == "BTC"


def test_empty_decision_id():

    try:
        DecisionContext(
            decision_id=""
        )

        assert False

    except ValueError:
        assert True