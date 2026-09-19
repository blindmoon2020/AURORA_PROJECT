from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from .base import DomainEvent



@dataclass(frozen=True)
class PortfolioCreatedEvent(DomainEvent):
    """
    Raised when a new portfolio
    is created.
    """

    portfolio_id: UUID

    account_id: UUID

    name: str





@dataclass(frozen=True)
class PortfolioActivatedEvent(DomainEvent):
    """
    Raised when a portfolio
    becomes active.
    """

    portfolio_id: UUID





@dataclass(frozen=True)
class PortfolioSuspendedEvent(DomainEvent):
    """
    Raised when portfolio operations
    are temporarily suspended.
    """

    portfolio_id: UUID





@dataclass(frozen=True)
class PortfolioClosedEvent(DomainEvent):
    """
    Raised when portfolio lifecycle
    is permanently closed.
    """

    portfolio_id: UUID





@dataclass(frozen=True)
class PortfolioAnalyticsSnapshotCreatedEvent(DomainEvent):
    """
    Raised when a portfolio analytics
    snapshot has been created.

    Used for:

    - Dashboard updates
    - Risk monitoring
    - Reporting
    - AI decision traceability
    - Historical analytics
    """

    portfolio_id: UUID

    total_value: Decimal

    currency: str

    exposure: Decimal

    risk_score: Decimal

    diversification: Decimal