from dataclasses import dataclass

from .contract import DataNormalizer

from .schema import CanonicalDataObject


@dataclass
class NormalizationEngine:
    """
    Executes raw data normalization workflow.
    """


    normalizer: DataNormalizer


    def process(
        self,
        data,
        **kwargs,
    ) -> CanonicalDataObject:


        return self.normalizer.normalize(
            data,
            **kwargs,
        )