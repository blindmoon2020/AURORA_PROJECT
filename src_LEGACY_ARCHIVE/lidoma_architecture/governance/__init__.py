"""
LIDOMA Architecture Governance Layer.
"""

from .contracts import (
    ContractDescriptor,
)

from .rules import (
    ArchitectureRule,
)

from .compatibility import (
    CompatibilityChecker,
)

from .versioning import (
    ContractVersion,
)

from .financial_contracts import (
    FinancialModuleContract,
    ExecutionBoundaryRule,
    StrategyValidationRule,
    RiskGateRule,
    TradingAgentRule,
)

from .financial_runtime_contract import (
    FinancialRuntimeContract,
)

from .financial_validator import (
    FinancialRuntimeValidator,
)


__all__ = [

    "ContractDescriptor",

    "ArchitectureRule",

    "CompatibilityChecker",

    "ContractVersion",

    "FinancialModuleContract",

    "ExecutionBoundaryRule",

    "StrategyValidationRule",

    "RiskGateRule",

    "TradingAgentRule",

    "FinancialRuntimeContract",

    "FinancialRuntimeValidator",

]