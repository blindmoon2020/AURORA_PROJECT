from lidoma_engines.evolution import (
    AdaptationProposalRequest,
    DecisionAdaptationProposer,
    DecisionExperienceCapture,
    DecisionPatternExtractor,
    EvolutionGovernanceDecision,
    EvolutionRuntimeIntegration,
    EvolutionRuntimeRequest,
    ExperienceCaptureRequest,
    PatternExtractionRequest,
)


def build_adaptation():

    experience = DecisionExperienceCapture().capture(
        ExperienceCaptureRequest(
            decision_id="runtime.decision.alpha",
            outcome="success",
            lessons={
                "market": "crypto",
            },
        )
    )

    pattern = DecisionPatternExtractor().extract(
        PatternExtractionRequest(
            experience=experience,
            pattern_type="runtime_pattern",
            features={
                "symbol": "BTCUSDT",
            },
        )
    )

    return DecisionAdaptationProposer().propose(
        AdaptationProposalRequest(
            pattern=pattern,
            adjustment_type="runtime_adjustment",
            changes={
                "threshold": 0.8,
            },
        )
    )


def test_runtime_integration_flow():

    adaptation = build_adaptation()

    result = EvolutionRuntimeIntegration().process(
        EvolutionRuntimeRequest(
            adaptation=adaptation,
            reviewer="runtime_governance",
            reason="approved evolution candidate",
            decision=EvolutionGovernanceDecision.APPROVED,
        )
    )

    assert result.review.is_approved

    assert result.audit.audit.entity_id == (
        adaptation.adaptation_id
    )

    assert result.applied is False
import pytest

from lidoma_engines.evolution import (
    EvolutionRuntimeIntegration,
    EvolutionRuntimeRequest,
    EvolutionGovernanceDecision,
)


def test_runtime_rejects_empty_reviewer():

    with pytest.raises(ValueError):

        EvolutionRuntimeIntegration().process(
            EvolutionRuntimeRequest(
                adaptation=build_adaptation(),
                reviewer=" ",
                reason="valid",
                decision=EvolutionGovernanceDecision.APPROVED,
            )
        )


def test_runtime_rejects_empty_reason():

    with pytest.raises(ValueError):

        EvolutionRuntimeIntegration().process(
            EvolutionRuntimeRequest(
                adaptation=build_adaptation(),
                reviewer="governance",
                reason=" ",
                decision=EvolutionGovernanceDecision.APPROVED,
            )
        )