class ProviderWeightCalculator:
    """
    Calculates provider contribution weight.
    """


    def calculate(
        self,
        reliability: float,
    ) -> float:

        if reliability < 0:

            return 0.0


        if reliability > 1:

            return 1.0


        return reliability