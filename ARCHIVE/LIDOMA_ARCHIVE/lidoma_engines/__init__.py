"""LIDOMA Evolution Engine Foundation.

This package is intentionally separate from ``lidoma_core`` so optional
intelligence, AI, data, analysis, risk and plugin capabilities can evolve
without coupling the stable domain core to external providers.
"""

from .contracts import (
    AnalysisProvider,
    AIProvider,
    ExpertKnowledgeProvider,
    MarketSourceProvider,
    PluginProvider,
    ProviderDescriptor,
    ProviderKind,
    ProviderStatus,
)

from .provenance import ProvenanceRecord
from .registry import CapabilityRegistry, RegistryEntry
from .mandatory_catalog import build_mandatory_registry

from .context import DecisionContext
from .events import DomainEvent
from .knowledge import KnowledgeRecord
from .experience import DecisionExperience
from .patterns import DecisionPattern
from .adaptation import DecisionAdaptation
from .audit import AuditRecord
from .observability import ObservabilityRecord
from .errors import LIDOMAErrorRecord
from .health import HealthStatus

from .evolution import (
    ExperienceCaptureRequest,
    DecisionExperienceCapture,
    PatternExtractionRequest,
    DecisionPatternExtractor,
    AdaptationProposalRequest,
    DecisionAdaptationProposer,
    EvolutionPipeline,
    EvolutionPipelineResult,
    EvolutionGovernanceDecision,
    EvolutionGovernanceReview,
    EvolutionGovernanceGate,
    EvolutionAuditResult,
    EvolutionAuditBuilder,
    EvolutionRuntimeRequest,
    EvolutionRuntimeResult,
    EvolutionRuntimeIntegration,
)


__all__ = [
    "AIProvider",
    "AnalysisProvider",
    "CapabilityRegistry",
    "ExpertKnowledgeProvider",
    "MarketSourceProvider",
    "PluginProvider",
    "ProvenanceRecord",
    "ProviderDescriptor",
    "ProviderKind",
    "ProviderStatus",
    "RegistryEntry",
    "build_mandatory_registry",

    "DecisionContext",
    "DomainEvent",
    "KnowledgeRecord",
    "DecisionExperience",
    "DecisionPattern",
    "DecisionAdaptation",
    "AuditRecord",
    "ObservabilityRecord",
    "LIDOMAErrorRecord",
    "HealthStatus",

    "ExperienceCaptureRequest",
    "DecisionExperienceCapture",
    "PatternExtractionRequest",
    "DecisionPatternExtractor",
    "AdaptationProposalRequest",
    "DecisionAdaptationProposer",
    "EvolutionPipeline",
    "EvolutionPipelineResult",
    "EvolutionGovernanceDecision",
    "EvolutionGovernanceReview",
    "EvolutionGovernanceGate",
    "EvolutionAuditResult",
    "EvolutionAuditBuilder",
    "EvolutionRuntimeRequest",
    "EvolutionRuntimeResult",
    "EvolutionRuntimeIntegration",
]