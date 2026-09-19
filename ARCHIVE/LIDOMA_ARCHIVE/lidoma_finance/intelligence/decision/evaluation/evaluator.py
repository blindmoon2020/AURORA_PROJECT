class DecisionEvaluator:
    """
    Evaluates financial intelligence inputs.
    """


    def evaluate(
        self,
        request,
    ) -> dict:

        return {

            "decision": "hold",

            "reason":

                "Insufficient execution context",

        }