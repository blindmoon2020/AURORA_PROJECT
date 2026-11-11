"""
Backward-compatible DecisionContext import.

The canonical DecisionContext contract lives in
``lidoma_engines.context``. This module is retained so existing imports
from ``lidoma_engines.decision.decision_context`` continue to resolve to
the exact same class.
"""

from lidoma_engines.context import DecisionContext


__all__ = [
    "DecisionContext",
]