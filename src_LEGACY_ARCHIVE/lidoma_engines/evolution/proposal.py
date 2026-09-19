from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from lidoma_engines.adaptation import DecisionAdaptation
from lidoma_engines.patterns import DecisionPattern


@dataclass(frozen=True)
class AdaptationProposalRequest:

    pattern: DecisionPattern
    adjustment_type: str
    changes: Mapping[str, Any]

    def __post_init__(self) -> None:

        if not self.adjustment_type.strip():
            raise ValueError(
                "adjustment_type must not be empty"
            )

        if not isinstance(self.changes, Mapping):
            raise TypeError(
                "changes must be a mapping"
            )


class DecisionAdaptationProposer:
    """
    Creates adaptation proposals from discovered patterns.

    Does not:
    - execute adaptations
    - mutate strategies
    - bypass governance
    """

    def propose(
        self,
        request: AdaptationProposalRequest,
    ) -> DecisionAdaptation:

        return DecisionAdaptation(
            adaptation_id=str(uuid4()),
            source_pattern_id=(
                request.pattern.pattern_id
            ),
            adjustment_type=(
                request.adjustment_type.strip()
            ),
            changes=dict(request.changes),
        )