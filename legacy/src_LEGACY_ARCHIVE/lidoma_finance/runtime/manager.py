from dataclasses import dataclass

from lidoma_architecture.governance import (
    FinancialRuntimeContract,
    FinancialRuntimeValidator,
)


@dataclass
class FinancialRuntimeManager:

    validator: FinancialRuntimeValidator


    def start(
        self,
        contract: FinancialRuntimeContract,
    ) -> bool:

        return self.validator.validate(
            contract
        )