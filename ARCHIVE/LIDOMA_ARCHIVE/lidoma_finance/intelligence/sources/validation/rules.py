from dataclasses import dataclass


@dataclass(frozen=True)
class SourceValidationRules:
    """
    Validation requirements for external sources.
    """


    require_identity: bool = True

    require_category: bool = True

    require_access_method: bool = True

    minimum_trust_score: float = 0.5


    def validate_trust_score(
        self,
        score: float,
    ) -> bool:

        return score >= self.minimum_trust_score