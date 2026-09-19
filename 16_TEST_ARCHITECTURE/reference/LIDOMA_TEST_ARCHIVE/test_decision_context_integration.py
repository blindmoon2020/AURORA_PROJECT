from lidoma_engines.decision import DecisionContext


def test_decision_context_available_from_decision_api():

    context = DecisionContext(
        decision_id="decision.integration.alpha",
        market_context={
            "symbol": "BTCUSDT",
            "regime": "bullish",
        },
        risk_context={
            "level": "low",
        },
    )

    assert context.decision_id == (
        "decision.integration.alpha"
    )

    assert context.market_context["symbol"] == (
        "BTCUSDT"
    )

    assert context.risk_context["level"] == (
        "low"
    )


def test_context_timestamp_is_timezone_aware():

    context = DecisionContext(
        decision_id="decision.time.alpha"
    )

    assert context.created_at.tzinfo is not None