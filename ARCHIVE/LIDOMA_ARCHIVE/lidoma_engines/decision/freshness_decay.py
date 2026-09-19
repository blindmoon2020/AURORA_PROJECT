from dataclasses import dataclass
from datetime import timedelta

from .freshness import (
    EvidenceFreshnessAssessment,
    FreshnessStatus,
)


@dataclass(frozen=True)
class FreshnessDecayAssessment:
    """
    Deterministic freshness influence applied to consensus weighting.

    The factor is deliberately kept outside DecisionEvidence so the original
    normalized evidence remains immutable and auditable.
    """

    evidence_id: str
    factor: float
    reason: str

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")

        if not 0.0 <= self.factor <= 1.0:
            raise ValueError(
                "freshness decay factor must be between 0 and 1"
            )

        if not self.reason.strip():
            raise ValueError("reason must not be empty")


class FreshnessDecayEvaluator:
    """
    Converts a freshness assessment into a deterministic consensus modifier.

    Rules:
    - FRESH -> 1.0
    - STALE -> linear decay from 1.0 at stale_after to 0.0 at expire_after
    - EXPIRED -> 0.0
    - FUTURE_DATED -> 0.0

    No provider, expert, website, broker, strategy, market, or asset class is
    hard-coded into the decay algorithm.
    """

    def evaluate(
        self,
        freshness: EvidenceFreshnessAssessment,
    ) -> FreshnessDecayAssessment:
        if freshness.status == FreshnessStatus.FRESH:
            return FreshnessDecayAssessment(
                evidence_id=freshness.evidence_id,
                factor=1.0,
                reason="freshness_decay:fresh_full_weight",
            )

        if freshness.status in (
            FreshnessStatus.EXPIRED,
            FreshnessStatus.FUTURE_DATED,
        ):
            return FreshnessDecayAssessment(
                evidence_id=freshness.evidence_id,
                factor=0.0,
                reason=(
                    "freshness_decay:"
                    f"{freshness.status.value.lower()}_zero_weight"
                ),
            )

        stale_window = (
            freshness.expire_after
            - freshness.stale_after
        )

        if stale_window <= timedelta(0):
            raise ValueError(
                "freshness decay requires expire_after "
                "greater than stale_after"
            )

        stale_age = freshness.age - freshness.stale_after

        if stale_age <= timedelta(0):
            factor = 1.0
        else:
            elapsed_ratio = (
                stale_age.total_seconds()
                / stale_window.total_seconds()
            )

            factor = max(
                0.0,
                min(
                    1.0,
                    1.0 - elapsed_ratio,
                ),
            )

        return FreshnessDecayAssessment(
            evidence_id=freshness.evidence_id,
            factor=factor,
            reason=(
                "freshness_decay:stale_linear_decay:"
                f"factor={factor:.6f}"
            ),
        )