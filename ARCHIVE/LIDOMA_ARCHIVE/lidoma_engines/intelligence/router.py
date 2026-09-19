from dataclasses import dataclass
from .capability_matcher import CapabilityMatcher
from .expert_selector import ExpertSelector


@dataclass(frozen=True)
class IntelligenceRequest:
    task: str
    market: str
    timeframe: str


class IntelligenceRouter:

    def __init__(self):
        self.matcher = CapabilityMatcher()
        self.selector = ExpertSelector()

    def route(self, request):
        matches = self.matcher.match(request.task)

        capabilities = tuple(
            x.capability for x in matches
        )

        return {
            "capabilities": capabilities,
            "experts": self.selector.select(capabilities),
            "market": request.market,
            "timeframe": request.timeframe,
        }
