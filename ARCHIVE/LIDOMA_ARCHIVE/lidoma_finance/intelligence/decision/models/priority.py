from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionPriority:
    """
    Decision execution priority model.
    """

    level: int

    label: str


    def is_high(self) -> bool:
        return self.level >= 8