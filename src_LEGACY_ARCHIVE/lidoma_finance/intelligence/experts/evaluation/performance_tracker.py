class PerformanceTracker:
    """
    Tracks expert historical performance.
    """


    def __init__(self):

        self._scores = {}


    def update(
        self,
        expert_id,
        score,
    ):

        self._scores[
            expert_id
        ] = score


    def get_score(
        self,
        expert_id,
    ):

        return self._scores.get(
            expert_id,
            0.0,
        )