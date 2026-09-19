from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, Tuple


class ExecutionEnvironment(str, Enum):
    DEV = "DEV"
    TEST = "TEST"
    STAGING = "STAGING"
    LIVE = "LIVE"


class ExecutionDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class ExecutionBlockReason(str, Enum):
    NONE = "NONE"
    POLICY_MISSING = "POLICY_MISSING"
    INVALID_REQUEST = "INVALID_REQUEST"
    LIVE_EXECUTION_DISABLED = "LIVE_EXECUTION_DISABLED"
    INVALID_ENVIRONMENT = "INVALID_ENVIRONMENT"
    AI_NOT_AUTHORIZED = "AI_NOT_AUTHORIZED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    HUMAN_APPROVAL_UNVERIFIED = "HUMAN_APPROVAL_UNVERIFIED"
    AUDIT_REQUIRED = "AUDIT_REQUIRED"
    AUDIT_UNVERIFIED = "AUDIT_UNVERIFIED"
    EMERGENCY_STOP_ACTIVE = "EMERGENCY_STOP_ACTIVE"


class ExecutionActor(str, Enum):
    AI = "AI"
    HUMAN = "HUMAN"
    SYSTEM = "SYSTEM"


ApprovalVerifier = Callable[[str, str], bool]
AuditVerifier = Callable[[str, str], bool]


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    live_execution_enabled: bool = False
    require_human_approval: bool = True
    require_audit: bool = True
    allow_ai_execution: bool = False
    allowed_live_environments: Tuple[ExecutionEnvironment, ...] = (
        ExecutionEnvironment.LIVE,
    )

    def __post_init__(self) -> None:
        for name in (
            "live_execution_enabled",
            "require_human_approval",
            "require_audit",
            "allow_ai_execution",
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")

        if not isinstance(self.allowed_live_environments, tuple):
            raise TypeError("allowed_live_environments must be a tuple")
        if not self.allowed_live_environments:
            raise ValueError("allowed_live_environments must not be empty")
        if any(
            not isinstance(item, ExecutionEnvironment)
            for item in self.allowed_live_environments
        ):
            raise TypeError("allowed_live_environments contains invalid values")


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    trade_id: str
    actor: ExecutionActor
    environment: ExecutionEnvironment
    request_live_execution: bool = False
    human_approval_id: Optional[str] = None
    audit_event_id: Optional[str] = None
    emergency_stop: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.trade_id, str) or not self.trade_id.strip():
            raise ValueError("trade_id must be a non-blank string")
        if not isinstance(self.actor, ExecutionActor):
            raise TypeError("actor must be ExecutionActor")
        if not isinstance(self.environment, ExecutionEnvironment):
            raise TypeError("environment must be ExecutionEnvironment")
        if not isinstance(self.request_live_execution, bool):
            raise TypeError("request_live_execution must be bool")
        if not isinstance(self.emergency_stop, bool):
            raise TypeError("emergency_stop must be bool")

        for name, value in (
            ("human_approval_id", self.human_approval_id),
            ("audit_event_id", self.audit_event_id),
        ):
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{name} must be str or None")
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"{name} must not be blank")


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    decision: ExecutionDecision
    reason: ExecutionBlockReason
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, ExecutionDecision):
            raise TypeError("decision must be ExecutionDecision")
        if not isinstance(self.reason, ExecutionBlockReason):
            raise TypeError("reason must be ExecutionBlockReason")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be non-empty string")
        if self.decision is ExecutionDecision.ALLOW and self.reason is not ExecutionBlockReason.NONE:
            raise ValueError("ALLOW requires NONE reason")
        if self.decision is ExecutionDecision.BLOCK and self.reason is ExecutionBlockReason.NONE:
            raise ValueError("BLOCK requires non-NONE reason")


class ExecutionPolicyEngine:
    def __init__(
        self,
        policy: Optional[ExecutionPolicy],
        *,
        approval_verifier: Optional[ApprovalVerifier] = None,
        audit_verifier: Optional[AuditVerifier] = None,
    ) -> None:
        if policy is None:
            raise ValueError("ExecutionPolicy is required; fail closed")
        if not isinstance(policy, ExecutionPolicy):
            raise TypeError("policy must be ExecutionPolicy")
        if approval_verifier is not None and not callable(approval_verifier):
            raise TypeError("approval_verifier must be callable or None")
        if audit_verifier is not None and not callable(audit_verifier):
            raise TypeError("audit_verifier must be callable or None")

        self._policy = policy
        self._approval_verifier = approval_verifier
        self._audit_verifier = audit_verifier

    @property
    def policy(self) -> ExecutionPolicy:
        return self._policy

    def evaluate(self, request: ExecutionRequest) -> ExecutionResult:
        if not isinstance(request, ExecutionRequest):
            raise TypeError("request must be ExecutionRequest")

        if request.emergency_stop:
            return self._block(
                ExecutionBlockReason.EMERGENCY_STOP_ACTIVE,
                "Emergency stop is active.",
            )

        if not request.request_live_execution:
            return self._allow("Request does not ask for live execution.")

        if request.environment not in self._policy.allowed_live_environments:
            return self._block(
                ExecutionBlockReason.INVALID_ENVIRONMENT,
                "Live execution is not allowed in this environment.",
            )

        if request.environment is not ExecutionEnvironment.LIVE:
            return self._block(
                ExecutionBlockReason.INVALID_ENVIRONMENT,
                "Live execution requires the LIVE environment.",
            )

        if not self._policy.live_execution_enabled:
            return self._block(
                ExecutionBlockReason.LIVE_EXECUTION_DISABLED,
                "Live execution is disabled by policy.",
            )

        if request.actor is ExecutionActor.AI and not self._policy.allow_ai_execution:
            return self._block(
                ExecutionBlockReason.AI_NOT_AUTHORIZED,
                "AI actors cannot execute live trades directly.",
            )

        if self._policy.require_human_approval:
            if not request.human_approval_id:
                return self._block(
                    ExecutionBlockReason.HUMAN_APPROVAL_REQUIRED,
                    "Human approval evidence is required.",
                )
            if self._approval_verifier is None:
                return self._block(
                    ExecutionBlockReason.HUMAN_APPROVAL_UNVERIFIED,
                    "Human approval verifier is required to validate approval evidence.",
                )
            try:
                approved = bool(self._approval_verifier(request.human_approval_id, request.trade_id))
            except Exception:
                approved = False
            if not approved:
                return self._block(
                    ExecutionBlockReason.HUMAN_APPROVAL_UNVERIFIED,
                    "Human approval evidence could not be verified for this trade.",
                )

        if self._policy.require_audit:
            if not request.audit_event_id:
                return self._block(
                    ExecutionBlockReason.AUDIT_REQUIRED,
                    "Audit evidence is required before execution.",
                )
            if self._audit_verifier is None:
                return self._block(
                    ExecutionBlockReason.AUDIT_UNVERIFIED,
                    "Audit verifier is required to validate audit evidence.",
                )
            try:
                audited = bool(self._audit_verifier(request.audit_event_id, request.trade_id))
            except Exception:
                audited = False
            if not audited:
                return self._block(
                    ExecutionBlockReason.AUDIT_UNVERIFIED,
                    "Audit evidence could not be verified for this trade.",
                )

        return self._allow("Execution request satisfies the execution policy.")

    @staticmethod
    def _allow(message: str) -> ExecutionResult:
        return ExecutionResult(
            ExecutionDecision.ALLOW,
            ExecutionBlockReason.NONE,
            message,
        )

    @staticmethod
    def _block(
        reason: ExecutionBlockReason,
        message: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            ExecutionDecision.BLOCK,
            reason,
            message,
        )
