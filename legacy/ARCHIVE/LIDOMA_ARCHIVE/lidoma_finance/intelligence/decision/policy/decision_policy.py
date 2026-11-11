class DecisionPolicy:
    """
    Defines financial decision rules.
    """


    def evaluate(
        self,
        request,
    ) -> str:

        if request.signal:

            return "BUY"


        return "HOLD"