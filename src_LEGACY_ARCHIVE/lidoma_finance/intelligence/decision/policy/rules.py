class DecisionPolicy:
    """
    Financial decision policy rules.
    """


    def apply(
        self,
        evaluation: dict,
    ) -> str:


        if evaluation.get(
            "validated"
        ):

            return "EXECUTE"


        return "HOLD"