from dataclasses import dataclass, field

from .query import SearchQuery

from .ranking import SearchRanking


@dataclass
class IntelligentSearchEngine:
    """
    LIDOMA internal intelligence retrieval engine.
    """


    index: dict[str, dict] = field(
        default_factory=dict
    )


    def index_entity(
        self,
        entity_id: str,
        data: dict,
    ):

        self.index[
            entity_id
        ] = data



    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchRanking]:


        results = []


        text = query.text.lower()


        for entity_id, data in self.index.items():

            content = str(data).lower()


            if text in content:

                results.append(

                    SearchRanking(

                        entity_id=entity_id,

                        relevance_score=1.0,

                        source_trust_score=data.get(
                            "trust_score",
                            0.5,
                        ),

                        final_score=data.get(
                            "trust_score",
                            0.5,
                        ),

                    )

                )


        results.sort(
            key=lambda item: item.final_score,
            reverse=True,
        )


        return results[
            :query.max_results
        ]