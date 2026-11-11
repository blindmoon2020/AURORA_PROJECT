from .contracts import ContractDescriptor


class CompatibilityChecker:


    def compatible(
        self,
        current: ContractDescriptor,
        target: ContractDescriptor,
    ) -> bool:

        return (
            current.name == target.name
            and
            current.version == target.version
        )