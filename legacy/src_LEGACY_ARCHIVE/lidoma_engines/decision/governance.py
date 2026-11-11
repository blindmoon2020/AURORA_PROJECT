from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .evidence import DecisionEvidence
from .freshness import (
    EvidenceFreshnessAssessment,
    EvidenceFreshnessEvaluator,
    FreshnessStatus,
)
from .freshness_decay import (
    FreshnessDecayAssessment,
    FreshnessDecayEvaluator,
)


class EvidenceGovernanceDisposition(str, Enum):
    ACCEPT = "ACCEPT"
    ACCEPT_WITH_WARNING = "ACCEPT_WITH_WARNING"
    REJECT = "REJECT"


@dataclass(frozen=True)
class GovernedEvidence:
    evidence: DecisionEvidence
    freshness: EvidenceFreshnessAssessment
    decay: FreshnessDecayAssessment
    disposition: EvidenceGovernanceDisposition
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(
            self.disposition,
            EvidenceGovernanceDisposition,
        ):
            raise TypeError(
                "disposition must be an "
                "EvidenceGovernanceDisposition"
            )

        if not self.reasons:
            raise ValueError(
                "governed evidence requires at least one reason"
            )

        if any(not reason.strip() for reason in self.reasons):
            raise ValueError(
                "governance reasons must not contain empty values"
            )

        if self.freshness.evidence_id != self.evidence.evidence_id:
            raise ValueError(
                "freshness evidence_id must match evidence"
            )

        if self.decay.evidence_id != self.evidence.evidence_id:
            raise ValueError(
                "decay evidence_id must match evidence"
            )

        if self.disposition == EvidenceGovernanceDisposition.REJECT:
            if self.decay.factor != 0.0:
                raise ValueError(
                    "rejected evidence must have zero decay factor"
                )

        if (
            self.disposition
            == EvidenceGovernanceDisposition.ACCEPT
            and self.freshness.status != FreshnessStatus.FRESH
        ):
            raise ValueError(
                "ACCEPT disposition requires FRESH evidence"
            )

        if (
            self.disposition
            == EvidenceGovernanceDisposition.ACCEPT_WITH_WARNING
            and self.freshness.status != FreshnessStatus.STALE
        ):
            raise ValueError(
                "ACCEPT_WITH_WARNING disposition requires STALE evidence"
            )

    @property
    def is_accepted(self) -> bool:
        return self.disposition in (
            EvidenceGovernanceDisposition.ACCEPT,
            EvidenceGovernanceDisposition.ACCEPT_WITH_WARNING,
        )

    @property
    def is_rejected(self) -> bool:
        return self.disposition == EvidenceGovernanceDisposition.REJECT

    @property
    def freshness_factor(self) -> float:
        return self.decay.factor


@dataclass(frozen=True)
class EvidenceGovernanceResult:
    accepted: tuple[GovernedEvidence, ...]
    rejected: tuple[GovernedEvidence, ...]
    evaluated_count: int

    def __post_init__(self) -> None:
        if self.evaluated_count < 0:
            raise ValueError(
                "evaluated_count must not be negative"
            )

        if (
            len(self.accepted)
            + len(self.rejected)
            != self.evaluated_count
        ):
            raise ValueError(
                "accepted + rejected must equal evaluated_count"
            )

        accepted_ids = {
            item.evidence.evidence_id
            for item in self.accepted
        }
        rejected_ids = {
            item.evidence.evidence_id
            for item in self.rejected
        }

        if len(accepted_ids) != len(self.accepted):
            raise ValueError(
                "accepted evidence IDs must be unique"
            )

        if len(rejected_ids) != len(self.rejected):
            raise ValueError(
                "rejected evidence IDs must be unique"
            )

        if accepted_ids & rejected_ids:
            raise ValueError(
                "evidence cannot be both accepted and rejected"
            )

    @property
    def accepted_evidence(
        self,
    ) -> tuple[DecisionEvidence, ...]:
        return tuple(
            item.evidence
            for item in self.accepted
        )

    @property
    def rejected_evidence(
        self,
    ) -> tuple[DecisionEvidence, ...]:
        return tuple(
            item.evidence
            for item in self.rejected
        )

    @property
    def accepted_count(self) -> int:
        return len(self.accepted)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

    @property
    def freshness_factors(self) -> dict[str, float]:
        return {
            item.evidence.evidence_id: item.freshness_factor
            for item in self.accepted
        }


class EvidenceGovernanceEngine:
    """
    Pre-consensus evidence governance.

    Phase 6.3.2 rules:
    - FRESH evidence -> ACCEPT with factor 1.0
    - STALE evidence -> ACCEPT_WITH_WARNING with deterministic decay
    - EXPIRED evidence -> REJECT with factor 0.0
    - FUTURE_DATED evidence -> REJECT with factor 0.0

    Rejected evidence remains available for audit and is never silently lost.
    """

    def __init__(
        self,
        freshness_evaluator: EvidenceFreshnessEvaluator | None = None,
        decay_evaluator: FreshnessDecayEvaluator | None = None,
    ) -> None:
        self.freshness_evaluator = (
            freshness_evaluator
            or EvidenceFreshnessEvaluator()
        )
        self.decay_evaluator = (
            decay_evaluator
            or FreshnessDecayEvaluator()
        )

    def evaluate_one(
        self,
        evidence: DecisionEvidence,
        *,
        evaluated_at: datetime | None = None,
    ) -> GovernedEvidence:
        freshness = self.freshness_evaluator.evaluate(
            evidence,
            evaluated_at=evaluated_at,
        )

        decay = self.decay_evaluator.evaluate(freshness)

        if freshness.status == FreshnessStatus.FRESH:
            return GovernedEvidence(
                evidence=evidence,
                freshness=freshness,
                decay=decay,
                disposition=EvidenceGovernanceDisposition.ACCEPT,
                reasons=(
                    freshness.reason,
                    decay.reason,
                    "governance:accepted",
                ),
            )

        if freshness.status == FreshnessStatus.STALE:
            return GovernedEvidence(
                evidence=evidence,
                freshness=freshness,
                decay=decay,
                disposition=(
                    EvidenceGovernanceDisposition.ACCEPT_WITH_WARNING
                ),
                reasons=(
                    freshness.reason,
                    decay.reason,
                    "governance:accepted_with_staleness_warning",
                ),
            )

        if freshness.status == FreshnessStatus.EXPIRED:
            return GovernedEvidence(
                evidence=evidence,
                freshness=freshness,
                decay=decay,
                disposition=EvidenceGovernanceDisposition.REJECT,
                reasons=(
                    freshness.reason,
                    decay.reason,
                    "governance:rejected_expired_evidence",
                ),
            )

        return GovernedEvidence(
            evidence=evidence,
            freshness=freshness,
            decay=decay,
            disposition=EvidenceGovernanceDisposition.REJECT,
            reasons=(
                freshness.reason,
                decay.reason,
                "governance:rejected_future_dated_evidence",
            ),
        )

    def evaluate(
        self,
        evidence: tuple[DecisionEvidence, ...],
        *,
        evaluated_at: datetime | None = None,
    ) -> EvidenceGovernanceResult:
        evidence_ids = [
            item.evidence_id
            for item in evidence
        ]

        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError(
                "evidence IDs must be unique before governance"
            )

        accepted: list[GovernedEvidence] = []
        rejected: list[GovernedEvidence] = []

        for item in evidence:
            governed = self.evaluate_one(
                item,
                evaluated_at=evaluated_at,
            )

            if governed.is_accepted:
                accepted.append(governed)
            else:
                rejected.append(governed)

        return EvidenceGovernanceResult(
            accepted=tuple(accepted),
            rejected=tuple(rejected),
            evaluated_count=len(evidence),
        )