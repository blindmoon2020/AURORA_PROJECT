from lidoma_engines.evolution import (
    AdaptationProposalRequest,
    DecisionAdaptationProposer,
    DecisionExperienceCapture,
    DecisionPatternExtractor,
    EvolutionPipeline,
    EvolutionPipelineResult,
    ExperienceCaptureRequest,
    PatternExtractionRequest,
)


def test_experience_capture_creates_linked_experience() -> None:
    capture = DecisionExperienceCapture()

    experience = capture.capture(
        ExperienceCaptureRequest(
            decision_id="decision-msft-001",
            outcome="success",
            lessons={
                "market": "equities",
                "instrument": "MSFT",
            },
        )
    )

    assert experience.experience_id
    assert experience.decision_id == "decision-msft-001"
    assert experience.outcome == "success"
    assert experience.lessons["market"] == "equities"
    assert experience.lessons["instrument"] == "MSFT"


def test_pattern_extraction_preserves_experience_lineage() -> None:
    capture = DecisionExperienceCapture()
    extractor = DecisionPatternExtractor()

    experience = capture.capture(
        ExperienceCaptureRequest(
            decision_id="decision-eurusd-001",
            outcome="failure",
            lessons={
                "market": "forex",
                "instrument": "EURUSD",
            },
        )
    )

    pattern = extractor.extract(
        PatternExtractionRequest(
            experience=experience,
            pattern_type="failed_breakout",
            features={
                "market": "forex",
                "instrument": "EURUSD",
                "timeframe": "H1",
            },
        )
    )

    assert pattern.pattern_id
    assert pattern.source_experience_id == experience.experience_id
    assert pattern.pattern_type == "failed_breakout"
    assert pattern.features["instrument"] == "EURUSD"


def test_adaptation_proposal_preserves_pattern_lineage() -> None:
    capture = DecisionExperienceCapture()
    extractor = DecisionPatternExtractor()
    proposer = DecisionAdaptationProposer()

    experience = capture.capture(
        ExperienceCaptureRequest(
            decision_id="decision-xauusd-001",
            outcome="success",
            lessons={
                "market": "commodities",
                "instrument": "XAUUSD",
            },
        )
    )

    pattern = extractor.extract(
        PatternExtractionRequest(
            experience=experience,
            pattern_type="liquidity_sweep_reversal",
            features={
                "instrument": "XAUUSD",
                "timeframe": "M15",
            },
        )
    )

    adaptation = proposer.propose(
        AdaptationProposalRequest(
            pattern=pattern,
            adjustment_type="strategy_parameter_proposal",
            changes={
                "minimum_confirmation_count": 2,
            },
        )
    )

    assert adaptation.adaptation_id
    assert adaptation.source_pattern_id == pattern.pattern_id
    assert adaptation.adjustment_type == "strategy_parameter_proposal"
    assert adaptation.changes["minimum_confirmation_count"] == 2


def test_full_evolution_pipeline_preserves_lineage() -> None:
    pipeline = EvolutionPipeline()

    result = pipeline.evolve(
        decision_id="decision-spx-001",
        outcome="success",
        lessons={
            "market": "indices",
            "instrument": "SPX",
        },
        features={
            "market": "indices",
            "instrument": "SPX",
            "timeframe": "H4",
            "setup": "support_reclaim",
        },
        pattern_type="support_reclaim",
        adjustment_type="strategy_parameter_proposal",
        changes={
            "confirmation_required": True,
        },
    )

    assert isinstance(result, EvolutionPipelineResult)
    assert result.experience_id
    assert result.pattern_id
    assert result.adaptation_id

    assert len(
        {
            result.experience_id,
            result.pattern_id,
            result.adaptation_id,
        }
    ) == 3


def test_evolution_pipeline_is_multi_asset() -> None:
    pipeline = EvolutionPipeline()

    instruments = (
        ("equities", "MSFT"),
        ("forex", "EURUSD"),
        ("commodities", "XAUUSD"),
        ("crypto", "BTCUSDT"),
    )

    results = []

    for index, (market, instrument) in enumerate(
        instruments,
        start=1,
    ):
        result = pipeline.evolve(
            decision_id=f"decision-{index}",
            outcome="success",
            lessons={
                "market": market,
                "instrument": instrument,
            },
            features={
                "market": market,
                "instrument": instrument,
                "timeframe": "H1",
            },
            pattern_type="validated_setup",
            adjustment_type="research_proposal",
            changes={
                "instrument": instrument,
            },
        )

        results.append(result)

    assert len(results) == 4
    assert all(result.experience_id for result in results)
    assert all(result.pattern_id for result in results)
    assert all(result.adaptation_id for result in results)