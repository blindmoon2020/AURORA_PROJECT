from typing import Dict

from ..profile import ExpertProfile


class ExpertRegistry:
    """
    Runtime registry for expert profiles.
    """

    def __init__(self):
        self._experts: Dict[str, ExpertProfile] = {}


    def register(
        self,
        profile: ExpertProfile,
    ) -> None:
        """
        Register expert profile.
        """

        self._experts[
            profile.identity.expert_id
        ] = profile


    def get(
        self,
        expert_id: str,
    ) -> ExpertProfile | None:
        """
        Retrieve expert profile.
        """

        return self._experts.get(
            expert_id
        )


    def list_all(
        self,
    ) -> list[ExpertProfile]:
        """
        Return all registered experts.
        """

        return list(
            self._experts.values()
        )