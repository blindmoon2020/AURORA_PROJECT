"""
LIDOMA Architecture Governance Public API.
"""

from .governance.contracts import (
    ContractDescriptor,
)

from .governance.rules import (
    ArchitectureRule,
    ArchitectureRuleViolation,
)

from .governance.compatibility import (
    CompatibilityChecker,
)

from .governance.versioning import (
    ContractVersion,
    VersionPolicy,
)


__all__ = [
    "ContractDescriptor",
    "ArchitectureRule",
    "ArchitectureRuleViolation",
    "CompatibilityChecker",
    "ContractVersion",
    "VersionPolicy",
]