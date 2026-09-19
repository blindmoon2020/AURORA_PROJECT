class DecisionEvaluator:
    """
    Evaluates intelligence inputs
    before financial decision.
    """


    def evaluate(
        self,
        request,
    ) -> dict:


        return {

            "status": "evaluated",

            "request": request.request_id,

        }