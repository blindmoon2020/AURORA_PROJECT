from ..request import (
    FinancialDecisionRequest,
)

from ..response import (
    FinancialDecisionResponse,
)

from ..state import (
    DecisionState,
)



class FinancialDecisionEngine:
    """
    Core financial decision orchestration engine.
    """


    def __init__(
        self,
        evaluator=None,
        scorer=None,
        validator=None,
    ):

        self.evaluator = evaluator

        self.scorer = scorer

        self.validator = validator



    def evaluate(
        self,
        request: FinancialDecisionRequest,
    ) -> FinancialDecisionResponse:
        """
        Evaluate financial decision request.
        """


        state = DecisionState(
            status="evaluating",
        )


        score = (

            self.scorer.calculate(
                request
            )

            if self.scorer

            else 1.0

        )


        valid = (

            self.validator.validate(
                request
            )

            if self.validator

            else True

        )


        decision = (

            self.evaluator.evaluate(
                request
            )

            if self.evaluator

            else "HOLD"

        )


        return FinancialDecisionResponse(

            request_id=request.request_id,

            decision=decision,

            score=score,

            approved=valid,

            metadata={

                "state": state.status,

            },

        )