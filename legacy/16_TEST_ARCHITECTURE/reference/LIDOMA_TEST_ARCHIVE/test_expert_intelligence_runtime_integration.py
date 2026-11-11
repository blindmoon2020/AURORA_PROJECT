from lidoma_finance.intelligence.experts import (
    ExpertIntelligenceEngine,
    ExpertRegistry,
    ExpertReliabilityEngine,
    ExpertIdentity,
    ExpertProfile,
    ExpertReliability,
    ExpertRequest,
)


def create_runtime():

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

    engine, registry, _ = create_runtime()


    identity = ExpertIdentity(
        expert_id="expert-001",
        name="Quant Analyst",
        organization="LIDOMA",
        domain="quant",
    )


    profile = ExpertProfile(
        identity=identity,
        methodology="quantitative analysis",
        specialization=[
            "risk",
            "market",
        ],
    )


    registry.register(
        profile
    )


    result = registry.get(
        "expert-001"
    )


    assert result.identity.expert_id == "expert-001"



def test_expert_reliability_calculation():

    _, _, reliability_engine = create_runtime()


    reliability = ExpertReliability(

        expert_id="expert-001",

        accuracy=0.9,

        consistency=0.8,

        evidence_quality=0.95,

    )


    score = reliability_engine.calculate(
        reliability
    )


    assert score > 0.6



def test_expert_analysis_runtime():

    engine, registry, _ = create_runtime()


    identity = ExpertIdentity(

        expert_id="expert-002",

        name="Market Expert",

        organization="LIDOMA",

        domain="fundamental",

    )


    profile = ExpertProfile(

        identity=identity,

        methodology="fundamental analysis",

    )


    registry.register(
        profile
    )


    request = ExpertRequest(

        request_id="req-001",

        topic="BTC valuation",

        experts=[
            "expert-002"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None



def test_unknown_expert_handling():

    engine, _, _ = create_runtime()


    request = ExpertRequest(

        request_id="req-002",

        topic="unknown",

        experts=[
            "not-exist"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None



def test_multiple_expert_registry():

    _, registry, _ = create_runtime()


    for index in range(3):

        identity = ExpertIdentity(

            expert_id=f"expert-{index}",

            name=f"Expert {index}",

            organization="LIDOMA",

            domain="finance",

        )


        registry.register(

            ExpertProfile(

                identity=identity,

                methodology="research",

            )

        )


    experts = registry.list_all()


    assert len(experts) == 3