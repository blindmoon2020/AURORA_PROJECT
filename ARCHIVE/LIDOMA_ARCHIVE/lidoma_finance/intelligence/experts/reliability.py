from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class ExpertReliability:
    """
    Expert historical reliability score.
    """


    expert_id: str


    accuracy: float


    consistency: float


    evidence_quality: float



    def overall(
        self,
    ) -> float:

        return (

            self.accuracy

            *

            self.consistency

            *

            self.evidence_quality

        )