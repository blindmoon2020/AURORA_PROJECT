class IntelligenceScoreEngine:


    def calculate(
        self,
        signals
    ):

        if not signals:

            return 0


        total = 0
        weight = 0


        for signal in signals:

            total += (
                signal.score *
                signal.confidence
            )

            weight += signal.confidence


        if weight == 0:

            return 0


        return round(
            total / weight,
            2
        )