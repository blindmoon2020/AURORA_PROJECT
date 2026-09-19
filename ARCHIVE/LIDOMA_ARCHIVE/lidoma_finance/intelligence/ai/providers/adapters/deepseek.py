from dataclasses import dataclass

from .base import AIProviderAdapter


@dataclass
class DeepSeekAdapter(AIProviderAdapter):


    api_key: str | None = None


    @property
    def provider_id(self):

        return "deepseek"


    @property
    def capabilities(self):

        return [

            "reasoning",

            "quant_analysis",

            "coding",

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