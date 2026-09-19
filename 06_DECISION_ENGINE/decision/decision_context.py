"""
Backward-compatible DecisionContext import.

The canonical DecisionContext contract lives in
``from .context.context import DecisionContext``. This module is retained so existing imports
from .context.context import DecisionContext`` continue to resolve to
the exact same class.
"""

from .context.context import DecisionContext


__all__ = [
    "DecisionContext",
]