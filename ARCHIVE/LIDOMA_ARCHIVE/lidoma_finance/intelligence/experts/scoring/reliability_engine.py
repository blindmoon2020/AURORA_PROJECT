from ..reliability import ExpertReliability


class ExpertReliabilityEngine:
    """
    Calculates expert reliability score.
    """


    def calculate(
        self,
        reliability: ExpertReliability,
    ) -> float:
        """
        Calculate normalized reliability.
        """

        return reliability.overall()