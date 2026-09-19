from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityMatch:
    capability: str
    score: float


class CapabilityMatcher:

    def match(self, request: str):
        text = request.lower()
        result = []

        if "liquidity" in text or "smart money" in text:
            result += [
                CapabilityMatch("smart_money", 0.8),
                CapabilityMatch("market_structure", 0.8),
            ]

        if "fibonacci" in text:
            result.append(
                CapabilityMatch("fibonacci", 0.8)
            )

        if "volume" in text or "poc" in text:
            result.append(
                CapabilityMatch("fixed_range_volume_profile", 0.8)
            )

        if not result:
            result.append(
                CapabilityMatch("advanced_price_action", 0.5)
            )

        return tuple(result)
