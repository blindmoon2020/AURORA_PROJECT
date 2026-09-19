from lidoma_engines.intelligence import (
    IntelligenceRouter,
    IntelligenceRequest,
    KnowledgeArtifact,
)


def test_router():
    router = IntelligenceRouter()

    result = router.route(
        IntelligenceRequest(
            "liquidity sweep with fibonacci",
            "BTC",
            "4H",
        )
    )

    assert "smart_money" in result["capabilities"]
    assert "fibonacci" in result["capabilities"]


def test_artifact():
    item = KnowledgeArtifact(
        "expert.test",
        "price_action",
        "BTC",
        "4H",
        0.8,
    )

    assert item.confidence == 0.8
