from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from .evidence import DecisionEvidence


class FreshnessStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    FUTURE_DATED = "FUTURE_DATED"


@dataclass(frozen=True)
class EvidenceFreshnessPolicy:
    """
    Policy controlling how old decision evidence may be before it becomes
    stale or expired.

    The policy is capability-aware but remains provider-agnostic.

    Example:
    - market.microstructure may require very short TTL
    - fundamental.earnings may remain useful for much longer
    - macro.central_bank may have its own lifecycle

    No expert, AI provider, website, broker, or asset class is hard-coded here.
    """

    default_stale_after: timedelta = timedelta(minutes=30)
    default_expire_after: timedelta = timedelta(hours=4)
    maximum_future_skew: timedelta = timedelta(seconds=30)
    capability_stale_after: Mapping[str, timedelta] = field(
        default_factory=dict
    )
    capability_expire_after: Mapping[str, timedelta] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self._validate_positive_duration(
            "default_stale_after",
            self.default_stale_after,
        )
        self._validate_positive_duration(
            "default_expire_after",
            self.default_expire_after,
        )

        if self.default_expire_after <= self.default_stale_after:
            raise ValueError(
                "default_expire_after must be greater than "
                "default_stale_after"
            )

        if self.maximum_future_skew < timedelta(0):
            raise ValueError(
                "maximum_future_skew must not be negative"
            )

        normalized_stale = self._normalize_capability_mapping(
            self.capability_stale_after,
            "capability_stale_after",
        )
        normalized_expire = self._normalize_capability_mapping(
            self.capability_expire_after,
            "capability_expire_after",
        )

        all_capabilities = (
            set(normalized_stale)
            | set(normalized_expire)
        )

        for capability in all_capabilities:
            stale_after = normalized_stale.get(
                capability,
                self.default_stale_after,
            )
            expire_after = normalized_expire.get(
                capability,
                self.default_expire_after,
            )

            if expire_after <= stale_after:
                raise ValueError(
                    "expire_after must be greater than stale_after "
                    f"for capability '{capability}'"
                )

        object.__setattr__(
            self,
            "capability_stale_after",
            MappingProxyType(normalized_stale),
        )
        object.__setattr__(
            self,
            "capability_expire_after",
            MappingProxyType(normalized_expire),
        )

    @staticmethod
    def _validate_positive_duration(
        name: str,
        value: timedelta,
    ) -> None:
        if value <= timedelta(0):
            raise ValueError(f"{name} must be greater than zero")

    @classmethod
    def _normalize_capability_mapping(
        cls,
        values: Mapping[str, timedelta],
        field_name: str,
    ) -> dict[str, timedelta]:
        normalized: dict[str, timedelta] = {}

        for raw_capability, duration in values.items():
            capability = raw_capability.strip()

            if not capability:
                raise ValueError(
                    f"{field_name} capability must not be empty"
                )

            cls._validate_positive_duration(
                f"{field_name}[{capability}]",
                duration,
            )

            if capability in normalized:
                raise ValueError(
                    f"duplicate normalized capability: {capability}"
                )

            normalized[capability] = duration

        return normalized

    def stale_after_for(
        self,
        capability: str,
    ) -> timedelta:
        normalized = capability.strip()

        if not normalized:
            raise ValueError("capability must not be empty")

        return self.capability_stale_after.get(
            normalized,
            self.default_stale_after,
        )

    def expire_after_for(
        self,
        capability: str,
    ) -> timedelta:
        normalized = capability.strip()

        if not normalized:
            raise ValueError("capability must not be empty")

        return self.capability_expire_after.get(
            normalized,
            self.default_expire_after,
        )


@dataclass(frozen=True)
class EvidenceFreshnessAssessment:
    evidence_id: str
    status: FreshnessStatus
    age: timedelta
    stale_after: timedelta
    expire_after: timedelta
    evaluated_at: datetime
    reason: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")

        if not isinstance(self.status, FreshnessStatus):
            raise TypeError(
                "status must be a FreshnessStatus"
            )

        if (
            self.evaluated_at.tzinfo is None
            or self.evaluated_at.utcoffset() is None
        ):
            raise ValueError(
                "evaluated_at must be timezone-aware"
            )

        if self.stale_after <= timedelta(0):
            raise ValueError(
                "stale_after must be greater than zero"
            )

        if self.expire_after <= self.stale_after:
            raise ValueError(
                "expire_after must be greater than stale_after"
            )

        if not self.reason.strip():
            raise ValueError("reason must not be empty")

    @property
    def is_usable(self) -> bool:
        return self.status in (
            FreshnessStatus.FRESH,
            FreshnessStatus.STALE,
        )

    @property
    def is_fresh(self) -> bool:
        return self.status == FreshnessStatus.FRESH


class EvidenceFreshnessEvaluator:
    """
    Deterministically evaluates evidence age against policy.

    This component does not:
    - mutate evidence
    - call providers
    - call brokers
    - use system-local naive timestamps
    - infer freshness from provider names
    """

    def __init__(
        self,
        policy: EvidenceFreshnessPolicy | None = None,
    ) -> None:
        self.policy = policy or EvidenceFreshnessPolicy()

    def evaluate(
        self,
        evidence: DecisionEvidence,
        *,
        evaluated_at: datetime | None = None,
    ) -> EvidenceFreshnessAssessment:
        now = evaluated_at or datetime.now(timezone.utc)

        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError(
                "evaluated_at must be timezone-aware"
            )

        stale_after = self.policy.stale_after_for(
            evidence.capability
        )
        expire_after = self.policy.expire_after_for(
            evidence.capability
        )

        age = now - evidence.created_at

        if age < -self.policy.maximum_future_skew:
            return EvidenceFreshnessAssessment(
                evidence_id=evidence.evidence_id,
                status=FreshnessStatus.FUTURE_DATED,
                age=age,
                stale_after=stale_after,
                expire_after=expire_after,
                evaluated_at=now,
                reason="future_dated:evidence_timestamp_exceeds_allowed_skew",
            )

        if age < timedelta(0):
            age = timedelta(0)

        if age >= expire_after:
            return EvidenceFreshnessAssessment(
                evidence_id=evidence.evidence_id,
                status=FreshnessStatus.EXPIRED,
                age=age,
                stale_after=stale_after,
                expire_after=expire_after,
                evaluated_at=now,
                reason="expired:evidence_age_exceeds_expiration_policy",
            )

        if age >= stale_after:
            return EvidenceFreshnessAssessment(
                evidence_id=evidence.evidence_id,
                status=FreshnessStatus.STALE,
                age=age,
                stale_after=stale_after,
                expire_after=expire_after,
                evaluated_at=now,
                reason="stale:evidence_age_exceeds_freshness_policy",
            )

        return EvidenceFreshnessAssessment(
            evidence_id=evidence.evidence_id,
            status=FreshnessStatus.FRESH,
            age=age,
            stale_after=stale_after,
            expire_after=expire_after,
            evaluated_at=now,
            reason="fresh:evidence_within_freshness_policy",
        )