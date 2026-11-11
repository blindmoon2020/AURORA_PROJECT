from core.ai_interface import AIProvider
from models.ai_response import AIResponse



class LocalAI(AIProvider):


    def analyze(self,data):

        return AIResponse(

            provider="LOCAL_AI",

            module=data.get(
                "module",
                "UNKNOWN"
            ),

            decision="WAIT",

            score=50,

            confidence=0.5,

            explanation=[
                "Base AI adapter ready"
            ]

        )