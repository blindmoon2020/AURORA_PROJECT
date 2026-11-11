"""
LIDOMA Autonomous Source Intelligence Layer.
"""


from .contract import (
    SourceAdapter,
)


from .registry.source_registry import (
    SourceRegistry,
)


from .models import (

    SourceMetadata,

    DataProvenance,

    SourceReliability,

)


from .validation import (

    SourceValidationRules,

    ReliabilityScoreEngine,

    SourceValidator,

)


from .extraction import (

    DataExtractor,

    RawDataPayload,

    ExtractionPipeline,

)


from .normalization import (

    DataNormalizer,

    CanonicalDataObject,

    NormalizationEngine,

)


__all__ = [

    "SourceAdapter",

    "SourceRegistry",

    "SourceMetadata",

    "DataProvenance",

    "SourceReliability",

    "SourceValidationRules",

    "ReliabilityScoreEngine",

    "SourceValidator",

    "DataExtractor",

    "RawDataPayload",

    "ExtractionPipeline",

    "DataNormalizer",

    "CanonicalDataObject",

    "NormalizationEngine",

]