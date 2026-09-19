from enum import Enum


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """
    Order lifecycle states.

    Represents the lifecycle
    of an exchange order.
    """

    CREATED = "CREATED"

    SUBMITTED = "SUBMITTED"

    ACCEPTED = "ACCEPTED"

    PARTIALLY_FILLED = "PARTIALLY_FILLED"

    FILLED = "FILLED"

    CANCELLED = "CANCELLED"

    REJECTED = "REJECTED"

    EXPIRED = "EXPIRED"


class ExecutionStatus(str, Enum):
    """
    Execution lifecycle states.

    Represents the lifecycle
    of order execution.
    """

    CREATED = "CREATED"

    SUBMITTED = "SUBMITTED"

    PARTIAL = "PARTIAL"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"

    REJECTED = "REJECTED"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class TradeStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class MarketRegime(str, Enum):
    TRENDING = "TRENDING"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    UNKNOWN = "UNKNOWN"


class AccountType(str, Enum):
    """
    Trading account categories.
    """

    PERSONAL = "PERSONAL"

    PROP = "PROP"

    INSTITUTIONAL = "INSTITUTIONAL"

    BROKER = "BROKER"


class AccountStatus(str, Enum):
    """
    Account lifecycle states.
    """

    ACTIVE = "ACTIVE"

    SUSPENDED = "SUSPENDED"

    CLOSED = "CLOSED"