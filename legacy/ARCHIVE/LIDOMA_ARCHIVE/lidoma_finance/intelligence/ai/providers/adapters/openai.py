from dataclasses import dataclass

from .base import AIProviderAdapter


@dataclass
class OpenAIAdapter(AIProviderAdapter):


    api_key: str | None = None


    @property
    def provider_id(self):

        return "openai"


    @property
    def capabilities(self):

        return [

            "reasoning",

            "analysis",

            "financial_context",

        ]


    def generate(
        self,
        context,
        **kwargs,
    ):

        return {

            "provider": self.provider_id,

            "status": "adapter_ready",

            "context": context,

        }


    def health_check(self):

        return True