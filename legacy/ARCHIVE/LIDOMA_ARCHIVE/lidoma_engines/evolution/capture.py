from dataclasses import dataclass
from typing import Any, Mapping
from uuid import uuid4

from lidoma_engines.experience import DecisionExperience


@dataclass(frozen=True)
class ExperienceCaptureRequest:
    """
    Immutable input contract for converting an evaluated decision
    lifecycle into an evolution experience.
    """

    decision_id: str
    outcome: str
    lessons: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, str):
            raise TypeError("decision_id must be a string")

        if not self.decision_id.strip():
            raise ValueError("decision_id must not be empty")

        if not isinstance(self.outcome, str):
            raise TypeError("outcome must be a string")

        if not self.outcome.strip():
            raise ValueError("outcome must not be empty")

        if not isinstance(self.lessons, Mapping):
            raise TypeError("lessons must be a mapping")


class DecisionExperienceCapture:
    """
    Creates DecisionExperience records from explicit evaluated inputs.

    This component:
    - does not execute decisions
    - does not evaluate outcomes
    - does not mutate decision memory
    - does not mutate strategies
    - does not approve adaptations
    """

    def capture(
        self,
        request: ExperienceCaptureRequest,
    ) -> DecisionExperience:
        return DecisionExperience(
            experience_id=str(uuid4()),
            decision_id=request.decision_id.strip(),
            outcome=request.outcome.strip(),
            lessons=dict(request.lessons),
        )
