from lidoma_architecture.governance import (
    FinancialRuntimeContract,
    FinancialRuntimeValidator,
)

from lidoma_finance import (
    FinancialRuntimeManager,
)


def test_financial_runtime_activation():

    contract = FinancialRuntimeContract(
        module_name="lidoma_finance",
        state="APPROVED",
        production_ready=True,
    )


    validator = FinancialRuntimeValidator()


    manager = FinancialRuntimeManager(
        validator=validator,
    )


    result = manager.start(
        contract
    )


    assert result is True



def test_financial_runtime_block():

    contract = FinancialRuntimeContract(
        module_name="lidoma_finance",
        state="BLOCKED",
        production_ready=False,
    )


    validator = FinancialRuntimeValidator()


    manager = FinancialRuntimeManager(
        validator=validator,
    )


    result = manager.start(
        contract
    )


    assert result is False