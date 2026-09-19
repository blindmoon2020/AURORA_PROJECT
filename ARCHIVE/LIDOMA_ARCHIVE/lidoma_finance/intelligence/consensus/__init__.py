"""
LIDOMA AI Consensus Reasoning Domain.

Domain contracts and runtime components
for multi AI provider consensus evaluation.
"""


from .contract import (
    ConsensusContract,
)

from .request import (
    ConsensusRequest,
)

from .response import (
    ConsensusResponse,
)

from .score import (
    ConsensusScore,
)

from .confidence import (
    ConfidenceScore,
)


from .engine import (
    ConsensusEngine,
)

from .normalizer import (
    ResponseNormalizer,
)

from .evaluator import (
    AgreementEvaluator,
)

from .weighting import (
    ProviderWeightCalculator,
)


__all__ = [

    # Contracts

    "ConsensusContract",

    "ConsensusRequest",

    "ConsensusResponse",

    "ConsensusScore",

    "ConfidenceScore",


    # Runtime Engine

    "ConsensusEngine",

    "ResponseNormalizer",

    "AgreementEvaluator",

    "ProviderWeightCalculator",

]