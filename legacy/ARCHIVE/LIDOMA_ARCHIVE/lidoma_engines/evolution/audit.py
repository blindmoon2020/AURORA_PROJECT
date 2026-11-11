from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from lidoma_engines.audit import AuditRecord

from .governance import EvolutionGovernanceReview


@dataclass(frozen=True)
class EvolutionAuditResult:

    audit: AuditRecord

    governance_approved: bool


class EvolutionAuditBuilder:
    """
    Builds audit records for evolution governance reviews.

    Does not:
    - persist audit data
    - execute adaptations
    - mutate runtime state
    """

    def build(
        self,
        review: EvolutionGovernanceReview,
    ) -> EvolutionAuditResult:

        audit = AuditRecord(
            audit_id=str(uuid4()),
            entity_id=(
                review.adaptation.adaptation_id
            ),
            action=(
                "evolution_adaptation_review"
            ),
            details={
                "source_pattern_id": (
                    review.adaptation.source_pattern_id
                ),
                "adjustment_type": (
                    review.adaptation.adjustment_type
                ),
                "governance_decision": (
                    review.decision.value
                ),
                "reviewer": review.reviewer,
                "reason": review.reason,
                "reviewed_at": (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                ),
            },
        )

        return EvolutionAuditResult(
            audit=audit,
            governance_approved=(
                review.is_approved
            ),
        )