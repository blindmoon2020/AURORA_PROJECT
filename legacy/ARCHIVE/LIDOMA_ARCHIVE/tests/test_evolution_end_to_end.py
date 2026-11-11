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


def test_full_evolution_lifecycle():

    experience = DecisionExperienceCapture().capture(
        ExperienceCaptureRequest(
            decision_id="decision.e2e.alpha",
            outcome="success",
            lessons={
                "market": "crypto",
                "symbol": "BTCUSDT",
            },
        )
    )

    assert experience.experience_id


    pattern = DecisionPatternExtractor().extract(
        PatternExtractionRequest(
            experience=experience,
            pattern_type="successful_setup",
            features={
                "symbol": "BTCUSDT",
                "timeframe": "H1",
            },
        )
    )

    assert pattern.source_experience_id == (
        experience.experience_id
    )


    adaptation = DecisionAdaptationProposer().propose(
        AdaptationProposalRequest(
            pattern=pattern,
            adjustment_type="parameter_update",
            changes={
                "confidence_threshold": 0.8,
            },
        )
    )

    assert adaptation.source_pattern_id == (
        pattern.pattern_id
    )


    review = EvolutionGovernanceGate().review(
        adaptation=adaptation,
        decision=EvolutionGovernanceDecision.APPROVED,
        reviewer="system_governance",
        reason="validated evolution proposal",
    )

    assert review.is_approved


    audit_result = EvolutionAuditBuilder().build(
        review
    )

    assert audit_result.governance_approved
    assert (
        audit_result.audit.entity_id
        == adaptation.adaptation_id
    )