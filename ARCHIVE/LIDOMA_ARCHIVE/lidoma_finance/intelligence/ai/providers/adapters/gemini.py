from dataclasses import dataclass

from .base import AIProviderAdapter


@dataclass
class GeminiAdapter(AIProviderAdapter):


    api_key: str | None = None


    @property
    def provider_id(self):

        return "gemini"


    @property
    def capabilities(self):

        return [

            "multimodal",

            "reasoning",

            "research",

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