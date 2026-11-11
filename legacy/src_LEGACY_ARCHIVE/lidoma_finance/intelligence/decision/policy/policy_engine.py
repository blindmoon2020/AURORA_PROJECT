class DecisionPolicyEngine:
    """
    Applies financial decision policies.
    """


    def approve(
        self,
        score: float,
    ) -> bool:

        return score >= 0.7