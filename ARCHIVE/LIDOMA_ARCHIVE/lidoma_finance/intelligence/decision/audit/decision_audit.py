from datetime import datetime



class DecisionAudit:
    """
    Decision execution audit trail.
    """


    def record(
        self,
        decision: str,
    ) -> dict:

        return {

            "decision": decision,

            "timestamp": datetime.utcnow().isoformat(),

        }