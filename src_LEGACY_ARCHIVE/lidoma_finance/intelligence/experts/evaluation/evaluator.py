from ..reliability import ExpertReliability



class ExpertEvaluator:
    """
    Evaluates expert reliability.
    """



    def evaluate(
        self,
        reliability: ExpertReliability,
    ) -> float:

        return reliability.overall()