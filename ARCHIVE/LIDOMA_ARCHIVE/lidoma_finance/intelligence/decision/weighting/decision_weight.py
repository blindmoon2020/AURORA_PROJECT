class DecisionWeightCalculator:
    """
    Calculates decision confidence weight.
    """


    def calculate(
        self,
        confidence: float,
    ) -> float:

        if confidence < 0:

            return 0.0


        if confidence > 1:

            return 1.0


        return confidence