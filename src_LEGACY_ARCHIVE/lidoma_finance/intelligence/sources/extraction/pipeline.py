from dataclasses import dataclass

from .contract import DataExtractor

from .collector import RawDataPayload


@dataclass
class ExtractionPipeline:
    """
    Executes source extraction workflow.
    """


    extractor: DataExtractor


    def run(
        self,
        source_id: str,
        **kwargs,
    ) -> RawDataPayload:


        result = self.extractor.extract(
            source_id,
            **kwargs,
        )


        return result
