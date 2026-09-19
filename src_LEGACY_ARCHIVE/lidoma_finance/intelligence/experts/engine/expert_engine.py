"""
Expert Intelligence Runtime Engine.
"""


from ..request import ExpertRequest



class ExpertIntelligenceEngine:
    """
    Runtime engine for expert analysis execution.
    """


    def __init__(
        self,
        registry=None,
        reliability_engine=None,
    ):

        self.registry = registry

        self.reliability_engine = reliability_engine



    def analyze(
        self,
        request: ExpertRequest,
    ) -> dict:
        """
        Execute expert analysis request.
        """


        expert_results = []


        for expert_id in request.experts:


            profile = (

                self.registry.get(
                    expert_id
                )

                if self.registry

                else None

            )


            reliability = (

                self.reliability_engine.evaluate(
                    expert_id
                )

                if self.reliability_engine

                else 1.0

            )


            expert_results.append(

                {

                    "expert_id": expert_id,

                    "profile": profile,

                    "reliability": reliability,

                    "analysis": "",

                }

            )


        return {

            "request_id":
                request.request_id,

            "topic":
                request.topic,

            "experts":
                expert_results,

        }