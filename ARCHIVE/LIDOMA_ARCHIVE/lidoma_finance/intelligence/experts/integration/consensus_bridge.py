class ConsensusBridge:
    """
    Connects Expert Intelligence
    with Consensus Engine.
    """


    def __init__(
        self,
        consensus_engine=None,
    ):

        self.consensus_engine = (
            consensus_engine
        )


    def submit(
        self,
        request,
        expert_outputs,
    ):

        if self.consensus_engine is None:

            return expert_outputs


        return self.consensus_engine.evaluate(
            request,
            expert_outputs,
        )