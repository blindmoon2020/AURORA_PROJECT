from lidoma_finance.intelligence.experts import (
    ExpertIdentity,
    ExpertProfile,
    ExpertReliability,
    ExpertRequest,
    ExpertRegistry,
    ExpertIntelligenceEngine,
    ExpertReliabilityEngine,
)


def test_expert_identity_creation():

    identity = ExpertIdentity(
        expert_id="expert-001",
        name="Technical Analyst",
        organization="LIDOMA",
        domain="technical_analysis",
    )

    assert identity.expert_id == "expert-001"



def test_expert_profile_creation():

    identity = ExpertIdentity(
        expert_id="expert-002",
        name="Fundamental Analyst",
        organization="LIDOMA",
        domain="fundamental",
    )

    profile = ExpertProfile(
        identity=identity,
        methodology="value_analysis",
        specialization=[
            "stocks",
            "macro",
        ],
    )

    assert profile.identity.expert_id == "expert-002"



def test_expert_registry_runtime():

    registry = ExpertRegistry()

    identity = ExpertIdentity(
        expert_id="expert-003",
        name="Quant Expert",
        organization="LIDOMA",
        domain="quant",
    )

    profile = ExpertProfile(
        identity=identity,
        methodology="quantitative",
    )

    registry.register(profile)

    result = registry.get(
        "expert-003"
    )

    assert result.identity.expert_id == "expert-003"



def test_reliability_engine():

    engine = ExpertReliabilityEngine()


    reliability = ExpertReliability(

        expert_id="expert-004",

        accuracy=0.9,

        consistency=0.8,

        evidence_quality=0.95,

    )


    score = engine.calculate(
        reliability
    )


    assert score > 0



def test_expert_intelligence_engine():

    engine = ExpertIntelligenceEngine()


    request = ExpertRequest(

        request_id="request-001",

        topic="BTC analysis",

        experts=[
            "expert-001"
        ],

    )


    response = engine.analyze(
        request
    )


    assert response is not None