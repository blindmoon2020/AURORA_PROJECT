from dataclasses import dataclass


@dataclass
class ContextAssembler:
    """
    Combines multiple intelligence inputs.
    """


    def assemble(
        self,
        *contexts,
    ):

        return {

            "contexts": list(contexts),

            "count": len(contexts),

        }