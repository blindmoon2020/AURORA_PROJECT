from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPolicy:

    policy_id: str

    max_risk_score: float


    def __post_init__(self):

        if not self.policy_id.strip():
            raise ValueError(
                "policy_id must not be empty"
            )

        if not 0 <= self.max_risk_score <= 1:
            raise ValueError(
                "max_risk_score must be between 0 and 1"
            )