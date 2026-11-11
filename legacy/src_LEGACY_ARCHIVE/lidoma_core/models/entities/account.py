from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from ..enums import (
    AccountType,
    AccountStatus,
)

from ..value_objects import (
    Money,
    Currency,
)


@dataclass
class Account:
    """
    Core trading account entity.

    Represents ownership and financial
    context of trading operations.

    Supports:

    - Personal accounts
    - Proprietary trading accounts
    - Institutional accounts
    - Broker accounts
    """

    name: str

    account_type: AccountType

    initial_balance: Money

    base_currency: Currency

    status: AccountStatus = AccountStatus.ACTIVE


    id: UUID = field(
        default_factory=uuid4,
        init=False,
    )


    created_at: datetime = field(
        default_factory=lambda:
            datetime.now(timezone.utc),
        init=False,
    )


    metadata: dict[str, object] = field(
        default_factory=dict
    )


    def __post_init__(self):
        """
        Validate account identity.
        """

        normalized_name = self.name.strip()

        if not normalized_name:
            raise ValueError(
                "Account name cannot be empty"
            )


        object.__setattr__(
            self,
            "name",
            normalized_name
        )


    def suspend(self) -> None:
        """
        Suspend active account.
        """

        if self.status != AccountStatus.ACTIVE:
            raise ValueError(
                "Only active accounts can be suspended"
            )

        self.status = AccountStatus.SUSPENDED


    def close(self) -> None:
        """
        Permanently close account.
        """

        if self.status == AccountStatus.CLOSED:
            raise ValueError(
                "Account already closed"
            )

        self.status = AccountStatus.CLOSED