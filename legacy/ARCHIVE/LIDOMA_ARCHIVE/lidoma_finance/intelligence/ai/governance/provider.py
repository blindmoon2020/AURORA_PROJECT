from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderIdentity:

    provider_id: str

    display_name: str

    organization: str


    def __post_init__(self):

        if not self.provider_id.strip():
            raise ValueError(
                "provider_id required"
            )

        if not self.display_name.strip():
            raise ValueError(
                "display_name required"
            )

        if not self.organization.strip():
            raise ValueError(
                "organization required"
            )