from dataclasses import dataclass


@dataclass(frozen=True)
class ContractVersion:

    major: int

    minor: int

    patch: int



@dataclass(frozen=True)
class VersionPolicy:

    allow_breaking_changes: bool = False