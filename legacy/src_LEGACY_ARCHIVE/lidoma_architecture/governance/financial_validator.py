from dataclasses import dataclass

from .financial_runtime_contract import (
    FinancialRuntimeContract,
)


@dataclass(frozen=True)
class FinancialRuntimeValidator:


    def validate(
        self,
        contract: FinancialRuntimeContract,
    ) -> bool:

        if contract.state == "BLOCKED":
            return False

        if not contract.production_ready:
            return False

        return True