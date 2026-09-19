"""
LIDOMA Intelligence Root Layer.
"""


from .ai import (
    AIProvider,
    AIProviderRegistry,
)


from .sources import (
    SourceAdapter,
    SourceRegistry,
)


from .knowledge import (
    KnowledgeEntity,
    IntelligenceMemory,
    KnowledgeGraph,
    MemoryKnowledgeStore,
)


from .search import (
    SearchQuery,
    SearchRanking,
    IntelligentSearchEngine,
)


from .context import (
    FinancialAIContext,
    FinancialContextBuilder,
    ContextAssembler,
)


__all__ = [

    "AIProvider",

    "AIProviderRegistry",

    "SourceAdapter",

    "SourceRegistry",

    "KnowledgeEntity",

    "IntelligenceMemory",

    "KnowledgeGraph",

    "MemoryKnowledgeStore",

    "SearchQuery",

    "SearchRanking",

    "IntelligentSearchEngine",

    "FinancialAIContext",

    "FinancialContextBuilder",

    "ContextAssembler",

]