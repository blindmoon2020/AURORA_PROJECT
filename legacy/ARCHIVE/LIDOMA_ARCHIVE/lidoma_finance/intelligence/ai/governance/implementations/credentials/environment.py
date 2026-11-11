import os

from ...credential import CredentialResolver


class EnvironmentCredentialResolver(
    CredentialResolver
):
    """
    Runtime environment credential resolver.
    """


    def resolve(
        self,
        key_reference: str,
    ) -> str:

        if not key_reference:

            raise ValueError(
                "credential reference required"
            )


        value = os.getenv(
            key_reference
        )


        if value is None:

            raise RuntimeError(
                "credential not found"
            )


        return value