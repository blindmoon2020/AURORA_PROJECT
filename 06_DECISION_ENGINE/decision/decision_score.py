from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionScore:
    """
    Backward-compatible Phase 6 foundation score.

    Phase 6.1 introduces evidence-first decisions. This class remains available
    for callers that still use the original three-score interface.
    """

    intelligence_score: float
    risk_score: float
    consensus_score: float

    def __post_init__(self) -> None:
        for value in (
            self.intelligence_score,
            self.risk_score,
            self.consensus_score,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("score must be between 0 and 1")

    def final_score(self) -> float:
        return (
            self.intelligence_score * 0.4
            + self.risk_score * 0.3
            + self.consensus_score * 0.3
        )
