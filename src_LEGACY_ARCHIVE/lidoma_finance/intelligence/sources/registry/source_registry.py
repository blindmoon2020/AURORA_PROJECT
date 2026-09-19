from dataclasses import dataclass, field

from ..contract import SourceAdapter


@dataclass
class SourceRegistry:


    sources: dict[str, SourceAdapter] = field(
        default_factory=dict
    )


    def register(
        self,
        source: SourceAdapter,
    ):

        self.sources[
            source.source_id
        ] = source


    def get(
        self,
        source_id: str,
    ) -> SourceAdapter:

        if source_id not in self.sources:
            raise KeyError(source_id)

        return self.sources[source_id]


    def available_sources(self):

        return list(
            self.sources.keys()
        )