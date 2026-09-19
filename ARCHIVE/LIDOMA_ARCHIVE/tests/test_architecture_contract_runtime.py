from lidoma_finance.intelligence.architecture import (
    ContractRuntimeValidator,
)


from lidoma_finance.intelligence.architecture.runtime import (
    RuntimeComponent,
)



class TestRuntime(
    RuntimeComponent
):

    def execute(
        self,
    ):
        return True



def test_runtime_contract_validation():

    validator = ContractRuntimeValidator()


    runtime = TestRuntime()


    assert validator.validate(
        runtime
    )


def test_runtime_contract_method():

    runtime = TestRuntime()


    assert runtime.validate_contract()