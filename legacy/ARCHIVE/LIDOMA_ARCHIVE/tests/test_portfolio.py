from uuid import uuid4

import pytest

from lidoma_core.models.entities import (
    Portfolio,
    PortfolioStatus,
)



def create_portfolio():

    return Portfolio(
        account_id=uuid4(),
        name="Main Investment Portfolio",
        base_currency="USD",
    )



def test_portfolio_creation():

    portfolio = create_portfolio()


    assert portfolio.name == (
        "Main Investment Portfolio"
    )


    assert portfolio.status == (
        PortfolioStatus.CREATED
    )


    assert portfolio.id is not None



def test_portfolio_activation():

    portfolio = create_portfolio()


    portfolio.activate()


    assert portfolio.status == (
        PortfolioStatus.ACTIVE
    )



def test_portfolio_suspend():

    portfolio = create_portfolio()

    portfolio.activate()

    portfolio.suspend()


    assert portfolio.status == (
        PortfolioStatus.SUSPENDED
    )



def test_portfolio_close():

    portfolio = create_portfolio()


    portfolio.close()


    assert portfolio.status == (
        PortfolioStatus.CLOSED
    )



def test_invalid_activation():

    portfolio = create_portfolio()


    portfolio.activate()


    with pytest.raises(ValueError):

        portfolio.activate()



def test_invalid_suspend():

    portfolio = create_portfolio()


    with pytest.raises(ValueError):

        portfolio.suspend()



def test_metadata_storage():

    portfolio = create_portfolio()


    portfolio.metadata["strategy"] = (
        "institutional"
    )


    assert (
        portfolio.metadata["strategy"]
        ==
        "institutional"
    )