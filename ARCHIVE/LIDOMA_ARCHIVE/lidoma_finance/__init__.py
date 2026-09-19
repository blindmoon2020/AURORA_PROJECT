"""
LIDOMA Financial Intelligence Operating System.

Phase 7 Foundation
Architecture Blueprint v3.0
"""

from .market import MarketData
from .strategy import StrategyDefinition
from .simulation import SimulationResult

from .execution import (
    TradeOrder,
    ExecutionApproval,
)

from .portfolio import Portfolio

from .risk import (
    FinancialRiskAssessment,
    RiskGate,
)

from .agents import TradingAgent

from .adapters import BrokerConnection

from .decision import (
    FinancialDecisionContext,
    FinancialDecision,
    FinancialDecisionEngine,
)

from .orchestration import (
    TradingWorkflow,
)

from .experience import (
    FinancialExperienceRecord,
)

from .evolution import (
    EvolutionFeedback,
)

from .learning import (
    LearningCycle,
)

from .runtime import (
    FinancialRuntimeManager,
)


__version__ = "3.0.0"


__all__ = [

    "MarketData",
    "StrategyDefinition",
    "SimulationResult",

    "TradeOrder",
    "ExecutionApproval",

    "Portfolio",

    "FinancialRiskAssessment",
    "RiskGate",

    "TradingAgent",

    "BrokerConnection",

    "FinancialDecisionContext",
    "FinancialDecision",
    "FinancialDecisionEngine",

    "TradingWorkflow",

    "FinancialExperienceRecord",

    "EvolutionFeedback",

    "LearningCycle",

    "FinancialRuntimeManager",

]