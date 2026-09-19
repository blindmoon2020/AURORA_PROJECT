from decimal import Decimal

from lidoma_core.models import (
    Account,
    AccountType,
    AccountStatus,
    Money,
    Currency,
)


def create_account():

    return Account(
        name="Main Trading Account",
        account_type=AccountType.PERSONAL,
        initial_balance=Money(
            Decimal("10000"),
            "USDT",
        ),
        base_currency=Currency(
            "USDT"
        ),
    )


def test_account_creation():

    account = create_account()

    assert account.name == "Main Trading Account"

    assert account.account_type == AccountType.PERSONAL

    assert account.status == AccountStatus.ACTIVE

    assert str(account.base_currency) == "USDT"



def test_account_suspend():

    account = create_account()

    account.suspend()

    assert account.status == AccountStatus.SUSPENDED



def test_account_close():

    account = create_account()

    account.close()

    assert account.status == AccountStatus.CLOSED