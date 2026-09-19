from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyResult:

    name: str

    score: float

    bias: str

    valid: bool

    reasons: tuple[str,...]