from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AIResponse:

    provider: str
    module: str
    decision: str
    score: float
    confidence: float
    explanation: List[str]


    def to_dict(self) -> Dict:

        return {

            "provider": self.provider,
            "module": self.module,
            "decision": self.decision,
            "score": self.score,
            "confidence": self.confidence,
            "explanation": self.explanation

        }