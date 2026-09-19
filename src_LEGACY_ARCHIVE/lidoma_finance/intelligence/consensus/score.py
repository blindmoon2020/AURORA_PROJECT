from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class ConsensusScore:
    """
    Agreement score between AI providers.
    """


    agreement: float


    reliability: float


    evidence_quality: float


    def overall(
        self,
    ) -> float:

        return (

            self.agreement

            *

            self.reliability

            *

            self.evidence_quality

        )