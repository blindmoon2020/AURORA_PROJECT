class DecisionScoreEngine:
    """
    Calculates decision confidence.
    """


    def calculate(
        self,
        evaluation: dict,
    ) -> float:


        if evaluation.get(
            "validated"
        ):

            return 1.0


        return 0.0