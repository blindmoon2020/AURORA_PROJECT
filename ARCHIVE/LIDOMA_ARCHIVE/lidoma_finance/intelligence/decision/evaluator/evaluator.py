class DecisionEvaluator:
    """
    Evaluates intelligence inputs.
    """


    def evaluate(
        self,
        request,
    ) -> dict:

        return {

            "validated": True,

            "request":

                request.request_id,

        }