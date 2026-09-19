from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any


class TradeSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class TradeStatus(str, Enum):
    CREATED = "CREATED"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


@dataclass
class TradeContract:
    """
    Canonical trade-domain contract for LUNA.

    Lifecycle:

        CREATED
            ↓
        APPROVED
            ↓
        SUBMITTED
            ↓
        PARTIALLY_FILLED
            ↓
        FILLED
            ↓
        CLOSED

    Rejection/cancellation are controlled terminal paths.

    The contract is intentionally mutable because trade lifecycle
    transitions update status and timestamps.
    """

    trade_id: str
    symbol: str
    broker_symbol: str
    broker_id: str

    side: TradeSide
    order_type: OrderType
    status: TradeStatus

    entry_price: float
    stop_loss: float
    take_profit: float
    volume: float

    risk_percent: float
    risk_amount: float

    strategy: str
    timeframe: str

    created_at: datetime
    approved_at: datetime | None = None
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    closed_at: datetime | None = None

    order_id: str | None = None
    position_id: str | None = None

    prop_account: bool = False
    prop_profile: str | None = None

    reason: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """
        Normalize supported enum strings and immediately validate
        the complete object.
        """

        self.side = self._coerce_enum(
            self.side,
            TradeSide,
            "side",
        )

        self.order_type = self._coerce_enum(
            self.order_type,
            OrderType,
            "order_type",
        )

        self.status = self._coerce_enum(
            self.status,
            TradeStatus,
            "status",
        )

        self.validate()

    @staticmethod
    def _coerce_enum(
        value: Any,
        enum_type: type[Enum],
        field_name: str,
    ) -> Any:
        if isinstance(
            value,
            enum_type,
        ):
            return value

        if isinstance(
            value,
            str,
        ):
            normalized = value.strip().upper()

            try:
                return enum_type(
                    normalized
                )
            except ValueError as exc:
                raise ValueError(
                    f"{field_name} has invalid value: {value}"
                ) from exc

        raise TypeError(
            f"{field_name} must be "
            f"{enum_type.__name__} or string"
        )

    @staticmethod
    def _validate_required_text(
        value: Any,
        field_name: str,
    ) -> str:
        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string"
            )

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                f"{field_name} cannot be empty"
            )

        return cleaned

    @staticmethod
    def _validate_optional_text(
        value: Any,
        field_name: str,
    ) -> None:
        if value is None:
            return

        if not isinstance(
            value,
            str,
        ):
            raise TypeError(
                f"{field_name} must be a string or None"
            )

        if not value.strip():
            raise ValueError(
                f"{field_name} cannot be empty when provided"
            )

    @staticmethod
    def _validate_positive_number(
        value: Any,
        field_name: str,
    ) -> None:
        if isinstance(
            value,
            bool,
        ):
            raise TypeError(
                f"{field_name} must be numeric"
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise TypeError(
                f"{field_name} must be numeric"
            )

        number = float(value)

        if not isfinite(number):
            raise ValueError(
                f"{field_name} must be finite"
            )

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero"
            )

    @staticmethod
    def _validate_timezone_aware_datetime(
        value: Any,
        field_name: str,
    ) -> None:
        if not isinstance(
            value,
            datetime,
        ):
            raise TypeError(
                f"{field_name} must be datetime"
            )

        if value.tzinfo is None:
            raise ValueError(
                f"{field_name} must be timezone-aware"
            )

        if value.utcoffset() is None:
            raise ValueError(
                f"{field_name} must have a valid timezone offset"
            )

    @staticmethod
    def _ensure_time_order(
        earlier: datetime,
        later: datetime,
        earlier_name: str,
        later_name: str,
    ) -> None:
        if later < earlier:
            raise ValueError(
                f"{later_name} cannot be earlier than "
                f"{earlier_name}"
            )

    def validate(self) -> None:
        """
        Validate the complete trade contract and all lifecycle
        invariants.
        """

        self._validate_required_text(
            self.trade_id,
            "trade_id",
        )

        self._validate_required_text(
            self.symbol,
            "symbol",
        )

        self._validate_required_text(
            self.broker_symbol,
            "broker_symbol",
        )

        self._validate_required_text(
            self.broker_id,
            "broker_id",
        )

        self._validate_required_text(
            self.strategy,
            "strategy",
        )

        self._validate_required_text(
            self.timeframe,
            "timeframe",
        )

        if not isinstance(
            self.side,
            TradeSide,
        ):
            raise TypeError(
                "side must be TradeSide"
            )

        if not isinstance(
            self.order_type,
            OrderType,
        ):
            raise TypeError(
                "order_type must be OrderType"
            )

        if not isinstance(
            self.status,
            TradeStatus,
        ):
            raise TypeError(
                "status must be TradeStatus"
            )

        self._validate_positive_number(
            self.entry_price,
            "entry_price",
        )

        self._validate_positive_number(
            self.stop_loss,
            "stop_loss",
        )

        self._validate_positive_number(
            self.take_profit,
            "take_profit",
        )

        self._validate_positive_number(
            self.volume,
            "volume",
        )

        self._validate_positive_number(
            self.risk_percent,
            "risk_percent",
        )

        self._validate_positive_number(
            self.risk_amount,
            "risk_amount",
        )

        self._validate_timezone_aware_datetime(
            self.created_at,
            "created_at",
        )

        for field_name, value in (
            ("approved_at", self.approved_at),
            ("submitted_at", self.submitted_at),
            ("filled_at", self.filled_at),
            ("closed_at", self.closed_at),
        ):
            if value is not None:
                self._validate_timezone_aware_datetime(
                    value,
                    field_name,
                )

        self._validate_optional_text(
            self.order_id,
            "order_id",
        )

        self._validate_optional_text(
            self.position_id,
            "position_id",
        )

        self._validate_optional_text(
            self.prop_profile,
            "prop_profile",
        )

        self._validate_optional_text(
            self.reason,
            "reason",
        )

        self._validate_optional_text(
            self.notes,
            "notes",
        )

        if not isinstance(
            self.prop_account,
            bool,
        ):
            raise TypeError(
                "prop_account must be boolean"
            )

        if self.prop_account:
            if not self.prop_profile:
                raise ValueError(
                    "prop_profile is required for "
                    "prop_account=True"
                )

        elif self.prop_profile is not None:
            raise ValueError(
                "prop_account must be True when "
                "prop_profile is provided"
            )

        if self.side == TradeSide.BUY:
            if self.stop_loss >= self.entry_price:
                raise ValueError(
                    "BUY stop_loss must be below entry_price"
                )

            if self.take_profit <= self.entry_price:
                raise ValueError(
                    "BUY take_profit must be above entry_price"
                )

        elif self.side == TradeSide.SELL:
            if self.stop_loss <= self.entry_price:
                raise ValueError(
                    "SELL stop_loss must be above entry_price"
                )

            if self.take_profit >= self.entry_price:
                raise ValueError(
                    "SELL take_profit must be below entry_price"
                )

        if self.approved_at is not None:
            self._ensure_time_order(
                self.created_at,
                self.approved_at,
                "created_at",
                "approved_at",
            )

        if self.submitted_at is not None:
            reference = (
                self.approved_at
                or self.created_at
            )

            self._ensure_time_order(
                reference,
                self.submitted_at,
                (
                    "approved_at"
                    if self.approved_at is not None
                    else "created_at"
                ),
                "submitted_at",
            )

        if self.filled_at is not None:
            reference = (
                self.submitted_at
                or self.approved_at
                or self.created_at
            )

            self._ensure_time_order(
                reference,
                self.filled_at,
                (
                    "submitted_at"
                    if self.submitted_at is not None
                    else (
                        "approved_at"
                        if self.approved_at is not None
                        else "created_at"
                    )
                ),
                "filled_at",
            )

        if self.closed_at is not None:
            reference = (
                self.filled_at
                or self.submitted_at
                or self.approved_at
                or self.created_at
            )

            self._ensure_time_order(
                reference,
                self.closed_at,
                (
                    "filled_at"
                    if self.filled_at is not None
                    else (
                        "submitted_at"
                        if self.submitted_at is not None
                        else (
                            "approved_at"
                            if self.approved_at is not None
                            else "created_at"
                        )
                    )
                ),
                "closed_at",
            )

        if self.status in {
            TradeStatus.SUBMITTED,
            TradeStatus.PARTIALLY_FILLED,
            TradeStatus.FILLED,
            TradeStatus.CLOSED,
        }:
            if not self.order_id:
                raise ValueError(
                    f"{self.status.value} trade requires order_id"
                )

        if self.status in {
            TradeStatus.PARTIALLY_FILLED,
            TradeStatus.FILLED,
            TradeStatus.CLOSED,
        }:
            if self.filled_at is None:
                raise ValueError(
                    f"{self.status.value} trade requires filled_at"
                )

        if self.status == TradeStatus.FILLED:
            if not self.position_id:
                raise ValueError(
                    "FILLED trade requires position_id"
                )

        if self.status == TradeStatus.CLOSED:
            if not self.position_id:
                raise ValueError(
                    "CLOSED trade requires position_id"
                )

    @property
    def entry(self) -> float:
        """
        Backward-compatible alias for the historical `entry` field.
        """

        return self.entry_price

    @property
    def risk_distance(self) -> float:
        if self.side == TradeSide.BUY:
            return (
                self.entry_price
                - self.stop_loss
            )

        return (
            self.stop_loss
            - self.entry_price
        )

    @property
    def reward_distance(self) -> float:
        if self.side == TradeSide.BUY:
            return (
                self.take_profit
                - self.entry_price
            )

        return (
            self.entry_price
            - self.take_profit
        )

    def risk_reward(self) -> float:
        self.validate()

        risk = self.risk_distance

        if risk <= 0:
            raise ValueError(
                "Calculated trade risk must be greater than zero"
            )

        reward = self.reward_distance

        if reward <= 0:
            raise ValueError(
                "Calculated trade reward must be greater than zero"
            )

        return round(
            reward / risk,
            2,
        )

    def is_ready_for_approval(self) -> bool:
        try:
            self.validate()
        except (
            ValueError,
            TypeError,
        ):
            return False

        return (
            self.status
            == TradeStatus.CREATED
        )

    def approve(
        self,
        approved_at: datetime | None = None,
    ) -> None:
        if not self.is_ready_for_approval():
            raise ValueError(
                "Trade is not ready for approval"
            )

        timestamp = (
            approved_at
            or datetime.now(timezone.utc)
        )

        self._validate_timezone_aware_datetime(
            timestamp,
            "approved_at",
        )

        self._ensure_time_order(
            self.created_at,
            timestamp,
            "created_at",
            "approved_at",
        )

        self.approved_at = timestamp
        self.status = TradeStatus.APPROVED

        self.validate()

    def mark_submitted(
        self,
        order_id: str,
        submitted_at: datetime | None = None,
    ) -> None:
        if self.status != TradeStatus.APPROVED:
            raise ValueError(
                "Only approved trades can be submitted"
            )

        order_id = self._validate_required_text(
            order_id,
            "order_id",
        )

        timestamp = (
            submitted_at
            or datetime.now(timezone.utc)
        )

        self._validate_timezone_aware_datetime(
            timestamp,
            "submitted_at",
        )

        reference = (
            self.approved_at
            or self.created_at
        )

        self._ensure_time_order(
            reference,
            timestamp,
            (
                "approved_at"
                if self.approved_at is not None
                else "created_at"
            ),
            "submitted_at",
        )

        self.order_id = order_id
        self.submitted_at = timestamp
        self.status = TradeStatus.SUBMITTED

        self.validate()

    def mark_partially_filled(
        self,
        position_id: str | None = None,
        filled_at: datetime | None = None,
    ) -> None:
        if self.status not in {
            TradeStatus.SUBMITTED,
            TradeStatus.PARTIALLY_FILLED,
        }:
            raise ValueError(
                "Only submitted or partially filled trades "
                "can become partially filled"
            )

        timestamp = (
            filled_at
            or datetime.now(timezone.utc)
        )

        self._validate_timezone_aware_datetime(
            timestamp,
            "filled_at",
        )

        reference = (
            self.submitted_at
            or self.approved_at
            or self.created_at
        )

        self._ensure_time_order(
            reference,
            timestamp,
            (
                "submitted_at"
                if self.submitted_at is not None
                else (
                    "approved_at"
                    if self.approved_at is not None
                    else "created_at"
                )
            ),
            "filled_at",
        )

        if position_id is not None:
            position_id = self._validate_required_text(
                position_id,
                "position_id",
            )

            self.position_id = position_id

        self.filled_at = timestamp
        self.status = TradeStatus.PARTIALLY_FILLED

        self.validate()

    def mark_filled(
        self,
        position_id: str | None = None,
        filled_at: datetime | None = None,
    ) -> None:
        if self.status not in {
            TradeStatus.SUBMITTED,
            TradeStatus.PARTIALLY_FILLED,
        }:
            raise ValueError(
                "Only submitted or partially filled trades "
                "can be filled"
            )

        timestamp = (
            filled_at
            or datetime.now(timezone.utc)
        )

        self._validate_timezone_aware_datetime(
            timestamp,
            "filled_at",
        )

        reference = (
            self.submitted_at
            or self.approved_at
            or self.created_at
        )

        self._ensure_time_order(
            reference,
            timestamp,
            (
                "submitted_at"
                if self.submitted_at is not None
                else (
                    "approved_at"
                    if self.approved_at is not None
                    else "created_at"
                )
            ),
            "filled_at",
        )

        if position_id is not None:
            position_id = self._validate_required_text(
                position_id,
                "position_id",
            )

            self.position_id = position_id

        if not self.position_id:
            raise ValueError(
                "FILLED trade requires position_id"
            )

        self.filled_at = timestamp
        self.status = TradeStatus.FILLED

        self.validate()

    def mark_closed(
        self,
        closed_at: datetime | None = None,
    ) -> None:
        if self.status not in {
            TradeStatus.FILLED,
            TradeStatus.PARTIALLY_FILLED,
        }:
            raise ValueError(
                "Only filled or partially filled trades "
                "can be closed"
            )

        timestamp = (
            closed_at
            or datetime.now(timezone.utc)
        )

        self._validate_timezone_aware_datetime(
            timestamp,
            "closed_at",
        )

        reference = (
            self.filled_at
            or self.submitted_at
            or self.approved_at
            or self.created_at
        )

        self._ensure_time_order(
            reference,
            timestamp,
            (
                "filled_at"
                if self.filled_at is not None
                else (
                    "submitted_at"
                    if self.submitted_at is not None
                    else (
                        "approved_at"
                        if self.approved_at is not None
                        else "created_at"
                    )
                )
            ),
            "closed_at",
        )

        if not self.position_id:
            raise ValueError(
                "CLOSED trade requires position_id"
            )

        self.closed_at = timestamp
        self.status = TradeStatus.CLOSED

        self.validate()

    def reject(
        self,
        reason: str | None = None,
    ) -> None:
        if self.status not in {
            TradeStatus.CREATED,
            TradeStatus.APPROVED,
        }:
            raise ValueError(
                "Only created or approved trades "
                "can be rejected"
            )

        if reason is not None:
            reason = self._validate_required_text(
                reason,
                "reason",
            )

        self.reason = reason
        self.status = TradeStatus.REJECTED

        self.validate()

    def cancel(
        self,
        reason: str | None = None,
    ) -> None:
        if self.status not in {
            TradeStatus.CREATED,
            TradeStatus.APPROVED,
            TradeStatus.SUBMITTED,
            TradeStatus.PARTIALLY_FILLED,
        }:
            raise ValueError(
                "Trade cannot be cancelled from "
                f"status {self.status.value}"
            )

        if reason is not None:
            reason = self._validate_required_text(
                reason,
                "reason",
            )

        self.reason = reason
        self.status = TradeStatus.CANCELLED

        self.validate()

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Return a JSON-compatible representation.
        """

        data = asdict(self)

        data["side"] = self.side.value
        data["order_type"] = (
            self.order_type.value
        )
        data["status"] = self.status.value

        for field_name in (
            "created_at",
            "approved_at",
            "submitted_at",
            "filled_at",
            "closed_at",
        ):
            value = data.get(field_name)

            if isinstance(
                value,
                datetime,
            ):
                data[field_name] = (
                    value.astimezone(
                        timezone.utc
                    ).isoformat()
                )

        return data

    def report(
        self,
    ) -> dict[str, Any]:
        """
        Backward-compatible reporting interface.
        """

        result = self.to_dict()

        result["RR"] = self.risk_reward()

        return result