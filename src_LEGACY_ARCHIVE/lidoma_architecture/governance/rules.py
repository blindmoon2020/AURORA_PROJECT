from dataclasses import dataclass


@dataclass(frozen=True)
class ArchitectureRuleViolation:

    rule: str

    message: str



@dataclass(frozen=True)
class ArchitectureRule:

    name: str

    description: str


    def validate(
        self,
        condition: bool,
    ) -> bool:

        if not condition:
            raise ArchitectureRuleViolation(
                rule=self.name,
                message=self.description,
            )

        return True