from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionImpact:
    """
    Expected decision impact model.
    """

    expected_gain: float

    expected_risk: float


    def net_value(self) -> float:

        return (
            self.expected_gain
            -
            self.expected_risk
        )