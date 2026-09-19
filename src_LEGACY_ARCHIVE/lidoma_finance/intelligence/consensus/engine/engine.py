from typing import List


from ..request import ConsensusRequest

from ..response import ConsensusResponse

from ..score import ConsensusScore

from ..confidence import ConfidenceScore



class ConsensusEngine:
    """
    Core multi AI consensus reasoning engine.

    Responsibilities:

    - Receive normalized AI responses
    - Evaluate agreement
    - Generate consensus result
    """


    def __init__(
        self,
        normalizer=None,
        evaluator=None,
        weighting=None,
    ):

        self.normalizer = normalizer

        self.evaluator = evaluator

        self.weighting = weighting



    def evaluate(
        self,
        request: ConsensusRequest,
        responses: List[dict],
    ) -> ConsensusResponse:
        """
        Generate consensus response.
        """


        normalized = (

            self.normalizer.normalize(
                responses
            )

            if self.normalizer

            else responses

        )


        score = (

            self.evaluator.calculate(
                normalized
            )

            if self.evaluator

            else ConsensusScore(
                agreement=1.0,
                reliability=1.0,
                evidence_quality=1.0,
            )

        )


        confidence = ConfidenceScore(

            value=score.overall(),

            reasoning="Consensus calculated",

        )


        final_answer = normalized[0][
            "content"
        ] if normalized else ""


        return ConsensusResponse(

            request_id=request.request_id,

            final_answer=final_answer,

            participating_providers=[

                item["provider"]

                for item in normalized

            ],

            metadata={

                "confidence":
                    confidence.value

            },

        )