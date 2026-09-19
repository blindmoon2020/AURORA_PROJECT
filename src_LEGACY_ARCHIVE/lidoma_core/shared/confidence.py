from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceScore:

    value: float


    def __post_init__(self):

        if self.value < 0.0:
            raise ValueError(
                "confidence must be >= 0"
            )

        if self.value > 1.0:
            raise ValueError(
                "confidence must be <= 1"
            )