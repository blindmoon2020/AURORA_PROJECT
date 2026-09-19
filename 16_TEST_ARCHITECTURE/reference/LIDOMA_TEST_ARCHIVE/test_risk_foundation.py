from lidoma_engines.risk import (
    RiskAssessment,
    RiskEngine,
    RiskEvent,
    RiskMetric,
    RiskPolicy,
)


def test_risk_assessment_creation():

    assessment = RiskAssessment(
        assessment_id="risk.alpha",
        portfolio_id="portfolio.alpha",
        risk_score=0.5,
        metrics={
            "volatility": 0.4
        },
    )

    assert assessment.portfolio_id == (
        "portfolio.alpha"
    )

    assert assessment.risk_score == 0.5


def test_risk_metric_creation():

    metric = RiskMetric(
        name="volatility",
        value=0.25,
        metadata={},
    )

    assert metric.name == "volatility"


def test_risk_policy_creation():

    policy = RiskPolicy(
        policy_id="default",
        max_risk_score=0.7,
    )

    assert policy.max_risk_score == 0.7


def test_risk_event_creation():

    event = RiskEvent(
        event_type="RiskAssessmentCreated",
        aggregate_id="risk.alpha",
    )

    assert event.event_type == (
        "RiskAssessmentCreated"
    )


def test_risk_engine_assessment():

    result = RiskEngine().assess(
        portfolio_id="portfolio.alpha",
        metrics={
            "volatility": 0.4,
            "drawdown": 0.2,
        },
    )

    assert isinstance(
        result,
        RiskAssessment,
    )

    assert result.risk_score == 0.3