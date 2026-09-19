from dataclasses import dataclass

from lidoma_engines.adaptation import DecisionAdaptation

from .audit import (
    EvolutionAuditBuilder,
    EvolutionAuditResult,
)

from .governance import (
    EvolutionGovernanceDecision,
    EvolutionGovernanceGate,
    EvolutionGovernanceReview,
)


@dataclass(frozen=True)
class EvolutionRuntimeRequest:

    adaptation: DecisionAdaptation

    reviewer: str

    reason: str

    decision: EvolutionGovernanceDecision


@dataclass(frozen=True)
class EvolutionRuntimeResult:

    review: EvolutionGovernanceReview

    audit: EvolutionAuditResult

    applied: bool


class EvolutionRuntimeIntegration:

    def __init__(self) -> None:

        self._governance = EvolutionGovernanceGate()

        self._audit = EvolutionAuditBuilder()


    def process(
        self,
        request: EvolutionRuntimeRequest,
    ) -> EvolutionRuntimeResult:

        self._validate_request(
            request
        )

        review = self._governance.review(
            adaptation=request.adaptation,
            decision=request.decision,
            reviewer=request.reviewer,
            reason=request.reason,
        )

        audit = self._audit.build(
            review
        )

        return EvolutionRuntimeResult(
            review=review,
            audit=audit,
            applied=False,
        )


    def _validate_request(
        self,
        request: EvolutionRuntimeRequest,
    ) -> None:

        if not isinstance(
            request,
            EvolutionRuntimeRequest,
        ):
            raise TypeError(
                "request must be EvolutionRuntimeRequest"
            )

        if not isinstance(
            request.adaptation,
            DecisionAdaptation,
        ):
            raise TypeError(
                "adaptation must be DecisionAdaptation"
            )

        if not isinstance(
            request.decision,
            EvolutionGovernanceDecision,
        ):
            raise TypeError(
                "decision must be EvolutionGovernanceDecision"
            )

        if not request.reviewer.strip():
            raise ValueError(
                "reviewer must not be empty"
            )

        if not request.reason.strip():
            raise ValueError(
                "reason must not be empty"
            )