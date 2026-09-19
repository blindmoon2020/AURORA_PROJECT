from dataclasses import dataclass
from typing import Any, Mapping

from lidoma_engines.adaptation import DecisionAdaptation
from lidoma_engines.patterns import DecisionPattern

from .capture import (
    DecisionExperienceCapture,
    ExperienceCaptureRequest,
)

from .extraction import (
    DecisionPatternExtractor,
    PatternExtractionRequest,
)

from .proposal import (
    AdaptationProposalRequest,
    DecisionAdaptationProposer,
)


@dataclass(frozen=True)
class EvolutionPipelineResult:
    experience_id: str
    pattern_id: str
    adaptation_id: str


class EvolutionPipeline:
    """
    Orchestrates the LIDOMA evolution flow.

    Flow:

    Decision Outcome
            |
            v
    Experience Capture
            |
            v
    Pattern Extraction
            |
            v
    Adaptation Proposal

    Does not:
    - execute decisions
    - mutate strategies
    - bypass governance
    - alter runtime decisions
    """

    def __init__(
        self,
        *,
        experience_capture: DecisionExperienceCapture | None = None,
        pattern_extractor: DecisionPatternExtractor | None = None,
        adaptation_proposer: DecisionAdaptationProposer | None = None,
    ) -> None:

        self.experience_capture = (
            experience_capture
            or DecisionExperienceCapture()
        )

        self.pattern_extractor = (
            pattern_extractor
            or DecisionPatternExtractor()
        )

        self.adaptation_proposer = (
            adaptation_proposer
            or DecisionAdaptationProposer()
        )


    def evolve(
        self,
        *,
        decision_id: str,
        outcome: str,
        lessons: Mapping[str, Any],
        features: Mapping[str, Any],
        pattern_type: str,
        adjustment_type: str,
        changes: Mapping[str, Any],
    ) -> EvolutionPipelineResult:

        experience = (
            self.experience_capture.capture(
                ExperienceCaptureRequest(
                    decision_id=decision_id,
                    outcome=outcome,
                    lessons=lessons,
                )
            )
        )


        pattern = (
            self.pattern_extractor.extract(
                PatternExtractionRequest(
                    experience=experience,
                    features=features,
                    pattern_type=pattern_type,
                )
            )
        )


        adaptation = (
            self.adaptation_proposer.propose(
                AdaptationProposalRequest(
                    pattern=pattern,
                    adjustment_type=adjustment_type,
                    changes=changes,
                )
            )
        )


        return EvolutionPipelineResult(
            experience_id=experience.experience_id,
            pattern_id=pattern.pattern_id,
            adaptation_id=adaptation.adaptation_id,
        )