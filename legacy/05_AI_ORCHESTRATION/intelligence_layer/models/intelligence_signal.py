from dataclasses import dataclass
from enum import Enum


class IntelligenceType(Enum):

    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"
    SENTIMENT = "SENTIMENT"
    MACRO = "MACRO"
    QUANT = "QUANT"



@dataclass
class IntelligenceSignal:

    source: str
    symbol: str
    intelligence_type: IntelligenceType
    score: float
    confidence: float
    message: str


    def output(self):

        return {

            "source": self.source,
            "symbol": self.symbol,
            "type": self.intelligence_type.value,
            "score": self.score,
            "confidence": self.confidence,
            "message": self.message

        }