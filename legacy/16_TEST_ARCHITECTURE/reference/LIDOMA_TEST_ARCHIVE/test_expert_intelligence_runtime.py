from lidoma_finance.intelligence.experts import (
    ExpertIdentity,
    ExpertProfile,
    ExpertReliability,
    ExpertRequest,
    ExpertRegistry,
    ExpertReliabilityEngine,
    ExpertIntelligenceEngine,
)


def create_expert_runtime():

    registry = ExpertRegistry()

    reliability_engine = ExpertReliabilityEngine()

    engine = ExpertIntelligenceEngine(
        registry=registry,
        reliability_engine=reliability_engine,
    )

    return (
        engine,
        registry,
        reliability_engine,
    )


def test_expert_registration_flow():

    engine, registry, _ = create_expert_runtime()


    identity = ExpertIdentity(

        expert_id="expert-001",

        name="Technical Analyst",

        organization="LIDOMA",

        domain="technical",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="price action",

        specialization=[
            "BTC",
            "market structure",
        ],

    )


    registry.register(
        profile
    )


    result = registry.get(
        "expert-001"
    )


    assert result.identity.expert_id == "expert-001"



def test_expert_reliability_evaluation():

    _, _, reliability_engine = create_expert_runtime()


    reliability = ExpertReliability(

        expert_id="expert-001",

        accuracy=0.9,

        consistency=0.8,

        evidence_quality=0.95,

    )


    score = reliability_engine.calculate(
        reliability
    )


    assert score > 0



def test_expert_analysis_runtime():

    engine, registry, _ = create_expert_runtime()


    identity = ExpertIdentity(

        expert_id="expert-002",

        name="Fundamental Analyst",

        organization="LIDOMA",

        domain="fundamental",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="macro analysis",

    )


    registry.register(
        profile
    )


    request = ExpertRequest(

        request_id="request-001",

        topic="BTC valuation",

        experts=[
            "expert-002"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None



def test_missing_expert_handling():

    engine, _, _ = create_expert_runtime()


    request = ExpertRequest(

        request_id="missing-001",

        topic="test",

        experts=[
            "unknown"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None



def test_expert_profile_metadata():

    identity = ExpertIdentity(

        expert_id="expert-003",

        name="Quant Researcher",

        organization="LIDOMA",

        domain="quant",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="statistical modeling",

        metadata={
            "version": "1.0"
        },

    )


    assert profile.metadata["version"] == "1.0"