from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable

from core.event_bus import InMemoryEventBus
from core.execution_policy import (
    ExecutionDecision,
    ExecutionEnvironment,
    ExecutionPolicy,
    ExecutionPolicyEngine,
    ExecutionRequest,
    ExecutionActor,
)
from core.event_contract import (
    EventContract,
    EventSeverity,
    EventSourceType,
    EventType,
)
from core.state_machine import (
    InvalidStateTransition,
    ExecutionState,
    StateEntityType,
    StateMachine,
)
from core.trade_contract import (
    TradeContract,
    TradeStatus,
)


class TradeLifecycleError(RuntimeError):
    """Base exception for trade lifecycle failures."""


class TradeLifecycleValidationError(TradeLifecycleError):
    """Raised when a lifecycle operation fails validation."""


class TradeLifecycleConsistencyError(TradeLifecycleError):
    """Raised when lifecycle state becomes internally inconsistent."""


@dataclass(frozen=True)
class TradeLifecycleResult:
    """
    Immutable result of a lifecycle operation.
    """

    trade_id: str
    previous_state: ExecutionState
    current_state: ExecutionState
    event_id: str
    success: bool
    message: str


class TradeLifecycle:
    """
    Atomic local lifecycle coordinator for one AURORA trade.

    Architectural separation:

    TradeContract.status
        Represents the operational trade/order status.

    StateMachine.current_state
        Represents the broader AURORA lifecycle state, including
        validation, risk, human approval and execution stages.

    These two state systems are intentionally NOT one-to-one.

    Example:

        TradeStatus.CREATED
        +
        ExecutionState.RISK_CHECK

    is valid because risk checking is a lifecycle stage performed
    before the operational TradeStatus changes.

    This class provides local atomicity between:
        TradeContract
        StateMachine

    Event publishing happens after the local state transaction succeeds.

    Distributed atomicity across an external database/message broker
    will later require an Outbox/transaction mechanism.
    """

    _STATE_STATUS_COMPATIBILITY: dict[
        ExecutionState,
        frozenset[TradeStatus],
    ] = {
        ExecutionState.CREATED: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.WAITING: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.CANDIDATE: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.VALIDATED: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.ANALYZING: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.REVIEW: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.RISK_CHECK: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.RISK_APPROVED: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.RISK_REJECTED: frozenset(
            {
                TradeStatus.CREATED,
                TradeStatus.REJECTED,
            }
        ),
        ExecutionState.HUMAN_APPROVAL: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.HUMAN_APPROVED: frozenset(
            {
                TradeStatus.CREATED,
            }
        ),
        ExecutionState.HUMAN_REJECTED: frozenset(
            {
                TradeStatus.CREATED,
                TradeStatus.REJECTED,
            }
        ),
        ExecutionState.APPROVED: frozenset(
            {
                TradeStatus.APPROVED,
            }
        ),
        ExecutionState.SUBMITTED: frozenset(
            {
                TradeStatus.SUBMITTED,
            }
        ),
        ExecutionState.PARTIALLY_FILLED: frozenset(
            {
                TradeStatus.PARTIALLY_FILLED,
            }
        ),
        ExecutionState.FILLED: frozenset(
            {
                TradeStatus.FILLED,
            }
        ),
        ExecutionState.OPEN: frozenset(
            {
                TradeStatus.FILLED,
            }
        ),
        ExecutionState.MANAGED: frozenset(
            {
                TradeStatus.FILLED,
            }
        ),
        ExecutionState.CLOSED: frozenset(
            {
                TradeStatus.CLOSED,
            }
        ),
        ExecutionState.CANCELLED: frozenset(
            {
                TradeStatus.CANCELLED,
            }
        ),
        ExecutionState.REJECTED: frozenset(
            {
                TradeStatus.REJECTED,
            }
        ),
        ExecutionState.FAILED: frozenset(
            {
                TradeStatus.REJECTED,
            }
        ),
        ExecutionState.EMERGENCY_STOP: frozenset(
            {
                TradeStatus.FILLED,
                TradeStatus.CLOSED,
            }
        ),
        ExecutionState.SAFE_MODE: frozenset(
            {
                TradeStatus.CREATED,
                TradeStatus.APPROVED,
                TradeStatus.SUBMITTED,
                TradeStatus.FILLED,
                TradeStatus.PARTIALLY_FILLED,
            }
        ),
    }

    def __init__(
        self,
        trade: TradeContract,
        event_bus: InMemoryEventBus,
        *,
        state_machine: StateMachine | None = None,
        producer_instance: str = "AURORA_TRADE_LIFECYCLE",
        execution_policy_engine: ExecutionPolicyEngine | None = None,
    ) -> None:
        if not isinstance(trade, TradeContract):
            raise TradeLifecycleValidationError(
                "trade must be a TradeContract"
            )

        if not isinstance(
            event_bus,
            InMemoryEventBus,
        ):
            raise TradeLifecycleValidationError(
                "event_bus must be an InMemoryEventBus"
            )

        if state_machine is not None:
            if not isinstance(
                state_machine,
                StateMachine,
            ):
                raise TradeLifecycleValidationError(
                    "state_machine must be a StateMachine"
                )

            if (
                state_machine.entity_type
                != StateEntityType.TRADE
            ):
                raise TradeLifecycleValidationError(
                    "state_machine must use TRADE entity type"
                )

        if not isinstance(
            producer_instance,
            str,
        ) or not producer_instance.strip():
            raise TradeLifecycleValidationError(
                "producer_instance cannot be empty"
            )

        trade.validate()

        self.trade = trade
        self.event_bus = event_bus

        self.state_machine = (
            state_machine
            or self._create_state_machine_from_trade_status(
                trade
            )
        )

        self.producer_instance = (
            producer_instance.strip()
        )

        self.execution_policy_engine = (
            execution_policy_engine
            or ExecutionPolicyEngine(ExecutionPolicy())
        )

        self._lock = RLock()

        self._assert_consistent_state()

    @staticmethod
    def _create_state_machine_from_trade_status(
        trade: TradeContract,
    ) -> StateMachine:
        """
        Build the initial lifecycle state from operational TradeStatus.
        """

        mapping: dict[
            TradeStatus,
            ExecutionState,
        ] = {
            TradeStatus.CREATED: ExecutionState.CREATED,
            TradeStatus.APPROVED: ExecutionState.APPROVED,
            TradeStatus.SUBMITTED: ExecutionState.SUBMITTED,
            TradeStatus.PARTIALLY_FILLED: (
                ExecutionState.PARTIALLY_FILLED
            ),
            TradeStatus.FILLED: ExecutionState.FILLED,
            TradeStatus.REJECTED: ExecutionState.REJECTED,
            TradeStatus.CANCELLED: ExecutionState.CANCELLED,
            TradeStatus.CLOSED: ExecutionState.CLOSED,
        }

        try:
            initial_state = mapping[
                trade.status
            ]
        except KeyError as exc:
            raise TradeLifecycleValidationError(
                f"Unsupported trade status: "
                f"{trade.status}"
            ) from exc

        return StateMachine(
            StateEntityType.TRADE,
            initial_state,
        )

    @property
    def current_state(self) -> ExecutionState:
        return self.state_machine.current_state

    def _assert_consistent_state(self) -> None:
        """
        Validate compatibility between TradeStatus and ExecutionState.

        This is compatibility validation, not equality validation.
        """

        allowed_statuses = (
            self._STATE_STATUS_COMPATIBILITY.get(
                self.current_state
            )
        )

        if allowed_statuses is None:
            raise TradeLifecycleConsistencyError(
                "No compatibility rule exists for state: "
                f"{self.current_state.value}"
            )

        if self.trade.status not in allowed_statuses:
            raise TradeLifecycleConsistencyError(
                "TradeContract and StateMachine are "
                "incompatible: "
                f"trade_status="
                f"{self.trade.status.value}, "
                f"state="
                f"{self.current_state.value}"
            )

    def _snapshot_trade(self) -> dict[str, Any]:
        """
        Capture mutable TradeContract lifecycle fields.
        """

        return {
            "status": self.trade.status,
            "approved_at": self.trade.approved_at,
            "submitted_at": self.trade.submitted_at,
            "filled_at": self.trade.filled_at,
            "closed_at": self.trade.closed_at,
            "order_id": self.trade.order_id,
            "position_id": self.trade.position_id,
        }

    def _snapshot_state_machine(
        self,
    ) -> tuple[ExecutionState, tuple[Any, ...]]:
        return self.state_machine.transaction_snapshot()

    def _restore_state_machine(
        self,
        snapshot: tuple[ExecutionState, tuple[Any, ...]],
    ) -> None:
        self.state_machine.restore_transaction_snapshot(snapshot)

    def _restore_trade_and_state(
        self,
        trade_snapshot: dict[str, Any],
        state_snapshot: tuple[ExecutionState, tuple[Any, ...]],
    ) -> None:
        self._restore_trade(trade_snapshot)
        self._restore_state_machine(state_snapshot)

    def _assert_execution_authorized(
        self,
        execution_request: ExecutionRequest,
    ) -> None:
        if execution_request.trade_id != self.trade.trade_id:
            raise TradeLifecycleValidationError(
                "execution_request.trade_id does not match trade"
            )

        result = self.execution_policy_engine.evaluate(
            execution_request
        )

        if result.decision is not ExecutionDecision.ALLOW:
            raise TradeLifecycleValidationError(
                "Execution policy blocked submission: "
                f"{result.reason.value}: {result.message}"
            )

    def _restore_trade(
        self,
        snapshot: dict[str, Any],
    ) -> None:
        """
        Restore TradeContract after failed local mutation.
        """

        self.trade.status = snapshot["status"]
        self.trade.approved_at = snapshot["approved_at"]
        self.trade.submitted_at = snapshot["submitted_at"]
        self.trade.filled_at = snapshot["filled_at"]
        self.trade.closed_at = snapshot["closed_at"]
        self.trade.order_id = snapshot["order_id"]
        self.trade.position_id = snapshot["position_id"]

    def _publish_event(
        self,
        event_type: EventType,
        *,
        previous_state: ExecutionState,
        current_state: ExecutionState,
        reason: str,
        severity: EventSeverity = EventSeverity.INFO,
        extra_payload: dict[str, Any] | None = None,
    ) -> EventContract:
        """
        Publish a lifecycle event after local commit.
        """

        payload: dict[str, Any] = {
            "trade_id": self.trade.trade_id,
            "symbol": self.trade.symbol,
            "broker_symbol": self.trade.broker_symbol,
            "broker_id": self.trade.broker_id,
            "previous_state": previous_state.value,
            "current_state": current_state.value,
            "trade_status": self.trade.status.value,
            "reason": reason,
        }

        if extra_payload:
            payload.update(
                extra_payload
            )

        event = EventContract.create(
            event_type=event_type,
            source_type=(
                EventSourceType.EXECUTION
            ),
            source_name="TradeLifecycle",
            payload=payload,
            aggregate_type="TRADE",
            aggregate_id=self.trade.trade_id,
            correlation_id=self.trade.trade_id,
            producer_instance=self.producer_instance,
            severity=severity,
        )

        self.event_bus.publish(event)

        return event

    def _commit(
        self,
        next_state: ExecutionState,
        reason: str,
        *,
        event_type: EventType,
        trade_mutator: Callable[
            [],
            None,
        ]
        | None = None,
        extra_payload: dict[str, Any] | None = None,
        severity: EventSeverity = EventSeverity.INFO,
    ) -> TradeLifecycleResult:
        """
        Execute one locally atomic lifecycle operation.

        Transaction sequence:

        1. Lock.
        2. Validate current consistency.
        3. Validate target transition.
        4. Snapshot TradeContract.
        5. Apply TradeContract mutation.
        6. Validate TradeContract.
        7. Apply StateMachine transition.
        8. Validate combined compatibility.
        9. Publish event.

        If a local mutation fails before state transition completes,
        TradeContract is restored.
        """

        with self._lock:
            self.trade.validate()
            self._assert_consistent_state()

            previous_state = (
                self.current_state
            )

            if not isinstance(
                next_state,
                ExecutionState,
            ):
                raise TradeLifecycleValidationError(
                    "next_state must be a ExecutionState"
                )

            if (
                not isinstance(
                    reason,
                    str,
                )
                or not reason.strip()
            ):
                raise TradeLifecycleValidationError(
                    "reason cannot be empty"
                )

            if not self.state_machine.can_transition_to(
                next_state
            ):
                raise TradeLifecycleValidationError(
                    "Invalid transition for TRADE: "
                    f"{previous_state.value} -> "
                    f"{next_state.value}"
                )

            trade_snapshot = self._snapshot_trade()
            state_snapshot = self._snapshot_state_machine()

            try:
                if trade_mutator is not None:
                    trade_mutator()

                self.trade.validate()

                self.state_machine.transition(
                    next_state,
                    reason,
                )

                self._assert_consistent_state()

            except Exception as exc:
                self._restore_trade_and_state(
                    trade_snapshot,
                    state_snapshot,
                )

                raise TradeLifecycleValidationError(
                    str(exc)
                ) from exc

            event = self._publish_event(
                event_type,
                previous_state=previous_state,
                current_state=next_state,
                reason=reason,
                severity=severity,
                extra_payload=extra_payload,
            )

            return TradeLifecycleResult(
                trade_id=self.trade.trade_id,
                previous_state=previous_state,
                current_state=next_state,
                event_id=event.event_id,
                success=True,
                message=reason.strip(),
            )

    def start_risk_check(
        self,
        reason: str = "Trade entered risk validation",
    ) -> TradeLifecycleResult:
        """
        CREATED -> RISK_CHECK.
        """

        if self.trade.status != TradeStatus.CREATED:
            raise TradeLifecycleValidationError(
                "Risk check requires CREATED TradeStatus"
            )

        return self._commit(
            ExecutionState.RISK_CHECK,
            reason,
            event_type=EventType.RISK_CHECKED,
        )

    def approve_risk(
        self,
        reason: str = "Trade passed risk validation",
    ) -> TradeLifecycleResult:
        """
        RISK_CHECK -> RISK_APPROVED.
        """

        return self._commit(
            ExecutionState.RISK_APPROVED,
            reason,
            event_type=EventType.RISK_APPROVED,
        )

    def reject_risk(
        self,
        reason: str = "Trade rejected by risk validation",
    ) -> TradeLifecycleResult:
        """
        RISK_CHECK -> RISK_REJECTED.
        """

        def reject_trade() -> None:
            self.trade.status = (
                TradeStatus.REJECTED
            )

        return self._commit(
            ExecutionState.RISK_REJECTED,
            reason,
            event_type=EventType.RISK_REJECTED,
            trade_mutator=reject_trade,
        )

    def request_human_approval(
        self,
        reason: str = "Trade requires human approval",
    ) -> TradeLifecycleResult:
        """
        RISK_APPROVED -> HUMAN_APPROVAL.
        """

        return self._commit(
            ExecutionState.HUMAN_APPROVAL,
            reason,
            event_type=EventType.DECISION_CREATED,
        )

    def approve_by_human(
        self,
        reason: str = "Trade approved by human operator",
    ) -> TradeLifecycleResult:
        """
        HUMAN_APPROVAL -> HUMAN_APPROVED.
        """

        return self._commit(
            ExecutionState.HUMAN_APPROVED,
            reason,
            event_type=EventType.DECISION_APPROVED,
        )

    def reject_by_human(
        self,
        reason: str = "Trade rejected by human operator",
    ) -> TradeLifecycleResult:
        """
        HUMAN_APPROVAL -> HUMAN_REJECTED.
        """

        def reject_trade() -> None:
            self.trade.status = (
                TradeStatus.REJECTED
            )

        return self._commit(
            ExecutionState.HUMAN_REJECTED,
            reason,
            event_type=EventType.DECISION_REJECTED,
            trade_mutator=reject_trade,
        )

    def approve(
        self,
        reason: str = "Trade approved for submission",
    ) -> TradeLifecycleResult:
        """
        HUMAN_APPROVED -> APPROVED.

        Synchronizes TradeContract to APPROVED.
        """

        return self._commit(
            ExecutionState.APPROVED,
            reason,
            event_type=EventType.DECISION_APPROVED,
            trade_mutator=self.trade.approve,
        )

    def submit(
        self,
        order_id: str,
        reason: str = "Trade submitted to broker",
        *,
        execution_request: ExecutionRequest | None = None,
    ) -> TradeLifecycleResult:
        """
        APPROVED -> SUBMITTED, guarded by ExecutionPolicyEngine.

        A missing execution request is treated as an explicit non-live TEST
        execution request, so existing deterministic lifecycle tests remain
        compatible while LIVE execution always requires an explicit request
        carrying verified approval and audit evidence.
        """

        if (
            not isinstance(order_id, str)
            or not order_id.strip()
        ):
            raise TradeLifecycleValidationError(
                "order_id cannot be empty"
            )

        request = execution_request or ExecutionRequest(
            trade_id=self.trade.trade_id,
            actor=ExecutionActor.SYSTEM,
            environment=ExecutionEnvironment.TEST,
            request_live_execution=False,
        )

        self._assert_execution_authorized(request)

        def submit_trade() -> None:
            self.trade.mark_submitted(
                order_id.strip()
            )

        return self._commit(
            ExecutionState.SUBMITTED,
            reason,
            event_type=EventType.ORDER_SUBMITTED,
            trade_mutator=submit_trade,
            extra_payload={
                "order_id": order_id.strip(),
                "execution_environment": request.environment.value,
                "live_execution_requested": request.request_live_execution,
            },
        )

    def fill(
        self,
        position_id: str | None = None,
        reason: str = "Trade filled by broker",
    ) -> TradeLifecycleResult:
        """
        SUBMITTED -> FILLED.
        """

        def fill_trade() -> None:
            self.trade.mark_filled(
                position_id
            )

        return self._commit(
            ExecutionState.FILLED,
            reason,
            event_type=EventType.ORDER_FILLED,
            trade_mutator=fill_trade,
            extra_payload={
                "position_id": position_id,
            },
        )

    def open_position(
        self,
        reason: str = "Filled trade converted to open position",
    ) -> TradeLifecycleResult:
        """
        FILLED -> OPEN.
        """

        return self._commit(
            ExecutionState.OPEN,
            reason,
            event_type=EventType.POSITION_OPENED,
        )

    def manage_position(
        self,
        reason: str = "Position entered managed state",
    ) -> TradeLifecycleResult:
        """
        OPEN -> MANAGED.
        """

        return self._commit(
            ExecutionState.MANAGED,
            reason,
            event_type=EventType.POSITION_UPDATED,
        )

    def emergency_stop(
        self,
        reason: str = "Emergency stop activated",
    ) -> TradeLifecycleResult:
        """
        OPEN/MANAGED -> EMERGENCY_STOP.
        """

        return self._commit(
            ExecutionState.EMERGENCY_STOP,
            reason,
            event_type=EventType.EMERGENCY_STOP,
            severity=EventSeverity.CRITICAL,
        )

    def close(
        self,
        reason: str = "Trade lifecycle closed",
    ) -> TradeLifecycleResult:
        """
        FILLED/OPEN/MANAGED/EMERGENCY_STOP -> CLOSED.
        """

        def close_trade() -> None:
            if self.trade.status in {
                TradeStatus.FILLED,
                TradeStatus.PARTIALLY_FILLED,
            }:
                self.trade.mark_closed()
                return

            if self.trade.status == TradeStatus.CLOSED:
                raise TradeLifecycleValidationError(
                    "Trade is already closed"
                )

        return self._commit(
            ExecutionState.CLOSED,
            reason,
            event_type=EventType.POSITION_CLOSED,
            trade_mutator=close_trade,
        )

    def snapshot(self) -> dict[str, Any]:
        """
        Return a complete lifecycle diagnostic snapshot.
        """

        with self._lock:
            self._assert_consistent_state()

            return {
                "trade_id": self.trade.trade_id,
                "symbol": self.trade.symbol,
                "broker_symbol": self.trade.broker_symbol,
                "broker_id": self.trade.broker_id,
                "trade_status": self.trade.status.value,
                "state_machine_state": (
                    self.current_state.value
                ),
                "state_history_count": len(
                    self.state_machine.history
                ),
                "risk_percent": self.trade.risk_percent,
                "risk_amount": self.trade.risk_amount,
                "risk_reward": self.trade.risk_reward(),
                "prop_account": self.trade.prop_account,
                "prop_profile": self.trade.prop_profile,
            }

    def health_check(self) -> dict[str, Any]:
        """
        Return lifecycle health and consistency status.
        """

        with self._lock:
            consistency = True

            try:
                self.trade.validate()
                self._assert_consistent_state()
            except (
                ValueError,
                TradeLifecycleConsistencyError,
            ):
                consistency = False

            return {
                "component": "TradeLifecycle",
                "status": (
                    "READY"
                    if consistency
                    else "DEGRADED"
                ),
                "trade_id": self.trade.trade_id,
                "state": self.current_state.value,
                "trade_status": self.trade.status.value,
                "consistent": consistency,
                "event_bus_handlers": (
                    self.event_bus.handler_count()
                ),
                "event_history": len(
                    self.event_bus.history()
                ),
            }
