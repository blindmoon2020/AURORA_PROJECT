from lidoma_engines.evolution import (
    AdaptationProposalRequest,
    DecisionAdaptationProposer,
    DecisionExperienceCapture,
    DecisionPatternExtractor,
    EvolutionAuditBuilder,
    EvolutionGovernanceDecision,
    EvolutionGovernanceGate,
    ExperienceCaptureRequest,
    PatternExtractionRequest,
)


def build_adaptation():
    experience = DecisionExperienceCapture().capture(
        ExperienceCaptureRequest(
            decision_id="decision.gov.001",
            outcome="success",
            lessons={
                "market": "crypto",
            },
        )
    )

    pattern = DecisionPatternExtractor().extract(
        PatternExtractionRequest(
            experience=experience,
            pattern_type="validated_pattern",
            features={
                "symbol": "BTCUSDT",
            },
        )
    )

    return DecisionAdaptationProposer().propose(
        AdaptationProposalRequest(
            pattern=pattern,
            adjustment_type="parameter_proposal",
            changes={
                "threshold": 2,
            },
        )
    )


def test_governance_approval():

    adaptation = build_adaptation()

    review = EvolutionGovernanceGate().review(
        adaptation=adaptation,
        decision=EvolutionGovernanceDecision.APPROVED,
        reviewer="governance",
        reason="validated",
    )

    assert review.is_approved is True
    assert review.adaptation is adaptation


def test_governance_rejection():

    adaptation = build_adaptation()

    review = EvolutionGovernanceGate().review(
        adaptation=adaptation,
        decision=EvolutionGovernanceDecision.REJECTED,
        reviewer="governance",
        reason="insufficient evidence",
    )

    assert review.is_approved is False


def test_audit_preserves_lineage():

    adaptation = build_adaptation()

    review = EvolutionGovernanceGate().review(
        adaptation=adaptation,
        decision=EvolutionGovernanceDecision.APPROVED,
        reviewer="governance",
        reason="validated",
    )

    result = EvolutionAuditBuilder().build(review)

    assert result.audit.entity_id == adaptation.adaptation_id
    assert (
        result.audit.details["source_pattern_id"]
        == adaptation.source_pattern_id
    )

    assert result.governance_approved is True