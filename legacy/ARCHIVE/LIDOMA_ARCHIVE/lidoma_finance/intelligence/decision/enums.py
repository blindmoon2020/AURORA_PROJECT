from enum import Enum


class DecisionStatus(Enum):
    """
    Decision lifecycle states.
    """

    CREATED = "created"

    ANALYZING = "analyzing"

    EVALUATING = "evaluating"

    APPROVED = "approved"

    REJECTED = "rejected"

    EXECUTED = "executed"