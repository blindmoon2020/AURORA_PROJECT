from dataclasses import dataclass
from typing import Literal


FinancialModuleType = Literal[
    "market",
    "strategy",
    "simulation",
    "execution",
    "portfolio",
    "risk",
    "agent",
    "adapter",
]


@dataclass(frozen=True)
class FinancialModuleContract:

    module_name: str

    module_type: FinancialModuleType

    version: str

    risk_required: bool = True


    def __post_init__(self):

        if not self.module_name.strip():
            raise ValueError(
                "module_name must not be empty"
            )

        if not self.version.strip():
            raise ValueError(
                "version must not be empty"
            )


@dataclass(frozen=True)
class ExecutionBoundaryRule:

    decision_must_be_separated: bool = True

    risk_check_required: bool = True


@dataclass(frozen=True)
class StrategyValidationRule:

    backtest_required: bool = True

    simulation_required: bool = True

    live_approval_required: bool = True


@dataclass(frozen=True)
class RiskGateRule:

    block_without_approval: bool = True

    max_risk_score: float = 0.7


@dataclass(frozen=True)
class TradingAgentRule:

    experience_tracking_required: bool = True

    evolution_feedback_required: bool = True