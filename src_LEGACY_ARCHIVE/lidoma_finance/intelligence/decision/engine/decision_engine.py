from ..request import DecisionRequest

from ..response import DecisionResponse



class DecisionEngine:
    """
    Core financial decision execution engine.
    """


    def __init__(
        self,
        evaluator=None,
        scorer=None,
        risk_manager=None,
    ):

        self.evaluator = evaluator

        self.scorer = scorer

        self.risk_manager = risk_manager



    def execute(
        self,
        request: DecisionRequest,
    ) -> DecisionResponse:
        """
        Execute decision pipeline.
        """


        evaluation = (

            self.evaluator.evaluate(request)

            if self.evaluator

            else {}

        )


        score = (

            self.scorer.calculate(
                evaluation
            )

            if self.scorer

            else 0.0

        )


        risk = (

            self.risk_manager.assess(
                request
            )

            if self.risk_manager

            else {}

        )


        return DecisionResponse(

            decision_id=request.request_id,

            action="HOLD",

            confidence=score,

            metadata={
                "risk": risk,
                "evaluation": evaluation,
            },

        )