from dataclasses import dataclass

from ..models import (
    SourceMetadata,
    SourceReliability,
)

from .rules import (
    SourceValidationRules,
)


@dataclass
class SourceValidator:
    """
    Validates external intelligence sources.
    """


    rules: SourceValidationRules


    def validate_metadata(
        self,
        metadata: SourceMetadata,
    ) -> bool:


        if self.rules.require_identity:

            if not metadata.source_id:
                return False


        if self.rules.require_category:

            if not metadata.category:
                return False


        if self.rules.require_access_method:

            if not metadata.access_method:
                return False


        return True



    def validate_reliability(
        self,
        reliability: SourceReliability,
    ) -> bool:

        return (
            reliability.approved
            and
            self.rules.validate_trust_score(
                reliability.trust_score
            )
        )