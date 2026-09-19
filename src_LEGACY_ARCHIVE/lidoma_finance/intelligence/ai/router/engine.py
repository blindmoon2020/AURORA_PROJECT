from dataclasses import dataclass, field

from .response import AIResponse


@dataclass
class AIReasoningRouter:

    providers: dict = field(
        default_factory=dict
    )


    def register_provider(
        self,
        provider,
    ):

        self.providers[
            provider.provider_id
        ] = provider



    def available_providers(self):

        return list(
            self.providers.keys()
        )



    def execute(
        self,
        context,
    ):

        responses = []


        for provider in self.providers.values():

            responses.append(
                provider.generate(
                    context
                )
            )


        return responses