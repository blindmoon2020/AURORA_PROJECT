"""
Decision State Models.
"""


from enum import (
    Enum,
)



class DecisionStatus(
    Enum
):
    """
    Decision lifecycle state.
    """


    PENDING = "pending"

    PROCESSING = "processing"

    COMPLETED = "completed"

    FAILED = "failed"



class DecisionState:
    """
    Decision runtime state container.
    """


    def __init__(
        self,
        status: DecisionStatus = DecisionStatus.PENDING,
    ):

        self.status = status