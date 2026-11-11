from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionRationale:
    """
    Decision reasoning explanation model.
    """

    summary: str

    factors: list[str]


    def has_factors(self) -> bool:
        return len(self.factors) > 0