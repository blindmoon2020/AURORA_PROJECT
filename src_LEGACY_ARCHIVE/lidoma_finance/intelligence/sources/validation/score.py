from dataclasses import dataclass


@dataclass(frozen=True)
class ReliabilityScoreEngine:
    """
    Calculates source reliability score.
    """


    def calculate(
        self,
        validation_count: int,
        data_quality: float,
        consistency: float,
    ) -> float:

        if validation_count < 0:
            raise ValueError(
                "validation_count cannot be negative"
            )

        if not 0 <= data_quality <= 1:
            raise ValueError(
                "data_quality must be between 0 and 1"
            )

        if not 0 <= consistency <= 1:
            raise ValueError(
                "consistency must be between 0 and 1"
            )


        validation_factor = min(
            validation_count / 100,
            1
        )


        score = (
            validation_factor * 0.3
            +
            data_quality * 0.4
            +
            consistency * 0.3
        )


        return round(
            score,
            4,
        )