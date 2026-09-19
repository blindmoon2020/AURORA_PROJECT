class ContractRuntimeValidator:
    """
    Validates contract/runtime compatibility.
    """


    REQUIRED_METHODS = [
        "validate_contract",
    ]


    def validate(
        self,
        runtime_object,
    ) -> bool:
        """
        Ensure runtime implementation
        follows contract rules.
        """


        for method in self.REQUIRED_METHODS:

            if not hasattr(
                runtime_object,
                method,
            ):

                return False


        return True