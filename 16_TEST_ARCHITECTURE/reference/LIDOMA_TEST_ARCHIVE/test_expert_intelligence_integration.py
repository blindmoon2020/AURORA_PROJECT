from lidoma_finance.intelligence.experts import (
    ExpertIntelligenceEngine,
    ExpertRegistry,
    ExpertReliabilityEngine,
    ExpertIdentity,
    ExpertProfile,
    ExpertReliability,
    ExpertRequest,
)


def create_expert_runtime():

    registry = ExpertRegistry()

    reliability = ExpertReliabilityEngine()

    engine = ExpertIntelligenceEngine(
        registry=registry,
        reliability_engine=reliability,
    )

    return engine, registry, reliability



def test_expert_registration_flow():

    engine, registry, _ = create_expert_runtime()


    identity = ExpertIdentity(

        expert_id="expert-001",

        name="Market Analyst",

        organization="LIDOMA",

        domain="crypto",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="technical analysis",

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



def test_expert_reliability_engine():

    _, _, reliability = create_expert_runtime()


    score = ExpertReliability(

        expert_id="expert-001",

        accuracy=0.9,

        consistency=0.8,

        evidence_quality=0.95,

    )


    value = reliability.evaluate(
        score
    )


    assert value > 0



def test_expert_analysis_runtime():

    engine, registry, _ = create_expert_runtime()


    identity = ExpertIdentity(

        expert_id="expert-002",

        name="Quant Expert",

        organization="LIDOMA",

        domain="quant",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="quant model",

    )


    registry.register(
        profile
    )


    request = ExpertRequest(

        request_id="req-001",

        topic="BTC analysis",

        experts=[
            "expert-002"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None



def test_unknown_expert_handling():

    engine, _, _ = create_expert_runtime()


    request = ExpertRequest(

        request_id="req-002",

        topic="market",

        experts=[
            "unknown"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None