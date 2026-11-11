from ...version import ProviderVersion


class ProviderVersionValidator:
    """
    Runtime compatibility validator.

    Responsibilities:

    - Validate provider version metadata
    - Validate model version
    - Validate schema compatibility
    """


    def validate(
        self,
        version: ProviderVersion,
    ) -> bool:

        if not version.provider_id:

            return False


        if not version.provider_version:

            return False


        if not version.model_version:

            return False


        if not version.schema_version:

            return False


        return True