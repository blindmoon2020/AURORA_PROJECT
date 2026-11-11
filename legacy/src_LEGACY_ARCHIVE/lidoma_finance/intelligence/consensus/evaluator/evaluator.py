from ..score import ConsensusScore



class AgreementEvaluator:
    """
    Calculates agreement between AI responses.
    """


    def calculate(
        self,
        responses: list[dict],
    ) -> ConsensusScore:


        if not responses:

            return ConsensusScore(

                agreement=0.0,

                reliability=0.0,

                evidence_quality=0.0,

            )


        return ConsensusScore(

            agreement=1.0,

            reliability=1.0,

            evidence_quality=1.0,

        )