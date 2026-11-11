from dataclasses import dataclass


@dataclass(frozen=True)
class SelectionResult:
    provider_id: str
    reason: str


class ExpertSelector:

    def select(self, capabilities):
        mapping = {
            "smart_money": "expert.aidin_jabarpour",
            "advanced_price_action": "expert.alireza_solimankhah_soli",
            "fundamental_analysis": "expert.kourosh_gerami",
        }

        return tuple(
            SelectionResult(
                mapping[c],
                "capability matched"
            )
            for c in capabilities
            if c in mapping
        )
