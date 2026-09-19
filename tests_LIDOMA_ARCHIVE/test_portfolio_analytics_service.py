from decimal import Decimal
from uuid import uuid4


from lidoma_core.models.entities import (
    Portfolio,
)


from lidoma_core.services import (
    PortfolioAnalyticsService,
)



def create_empty_portfolio():

    return Portfolio(
        account_id=uuid4(),
        name="Test",
    )




def test_total_value_empty_portfolio():

    portfolio = create_empty_portfolio()


    service = PortfolioAnalyticsService()


    value = service.total_value(
        portfolio
    )


    assert value.amount == Decimal("0")





def test_exposure_empty_portfolio():

    portfolio = create_empty_portfolio()


    service = PortfolioAnalyticsService()


    exposure = service.exposure(
        portfolio
    )


    assert exposure.value == Decimal("0")





def test_risk_score_empty_portfolio():

    portfolio = create_empty_portfolio()


    service = PortfolioAnalyticsService()


    score = service.risk_score(
        portfolio
    )


    assert score.value == Decimal("0")





def test_diversification_empty_portfolio():

    portfolio = create_empty_portfolio()


    service = PortfolioAnalyticsService()


    result = service.diversification(
        portfolio
    )


    assert result.value == Decimal("0")





def test_portfolio_analytics_snapshot():

    portfolio = create_empty_portfolio()


    service = PortfolioAnalyticsService()


    snapshot = service.snapshot(
        portfolio
    )


    assert snapshot.total_value.amount == Decimal("0")


    assert snapshot.exposure.value == Decimal("0")


    assert snapshot.risk_score.value == Decimal("0")


    assert (
        snapshot.diversification.value
        ==
        Decimal("0")
    )