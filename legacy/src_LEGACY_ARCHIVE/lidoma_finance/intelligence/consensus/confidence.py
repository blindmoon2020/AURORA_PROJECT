from dataclasses import (
    dataclass,
)



@dataclass(
    frozen=True
)
class ConfidenceScore:
    """
    Confidence evaluation model.
    """


    value: float


    reasoning: str


    def is_high(
        self,
    ) -> bool:

        return self.value >= 0.8