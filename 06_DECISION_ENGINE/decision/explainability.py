from dataclasses import dataclass

from .decision_context import DecisionContext
from .evidence import DecisionEvidence, EvidenceAggregate


@dataclass(frozen=True)
class DecisionTrace:
    request_id: str
    summary: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    conflict_ratio: float
    confidence: float


class ExplainabilityBuilder:
    """
    Produces a deterministic audit-friendly explanation trace.

    It does not call an LLM. A later AI explanation layer may render this trace
    into natural language without changing the underlying decision facts.
    """

    def build(
        self,
        context: DecisionContext,
        evidence: tuple[DecisionEvidence, ...],
        aggregate: EvidenceAggregate,
    ) -> DecisionTrace:
        summary: list[str] = [
            f"market={context.market}",
            f"timeframe={context.timeframe}",
            f"direction_score={aggregate.direction_score:.4f}",
            f"confidence={aggregate.confidence:.4f}",
            f"conflict_ratio={aggregate.conflict_ratio:.4f}",
            (
                "evidence="
                f"{aggregate.usable_evidence_count}/"
                f"{aggregate.total_evidence_count}"
            ),
        ]

        if context.asset_class:
            summary.append(f"asset_class={context.asset_class}")

        if context.instrument:
            summary.append(f"instrument={context.instrument}")

        for item in evidence:
            summary.append(
                f"{item.source_id}:{item.capability}:"
                f"{item.direction.value}:{item.reason}"
            )

        return DecisionTrace(
            request_id=context.request_id,
            summary=tuple(summary),
            evidence_ids=aggregate.evidence_ids,
            source_ids=aggregate.source_ids,
            conflict_ratio=aggregate.conflict_ratio,
            confidence=aggregate.confidence,
        )
