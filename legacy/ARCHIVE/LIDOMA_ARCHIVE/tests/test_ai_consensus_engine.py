from lidoma_finance.intelligence.consensus import (
    ConsensusEngine,
    ConsensusRequest,
    ResponseNormalizer,
    AgreementEvaluator,
    ProviderWeightCalculator,
    ConsensusScore,
    ConfidenceScore,
)


def test_consensus_request_creation():

    request = ConsensusRequest(

        request_id="req-001",

        query="BTC market analysis",

        providers=[
            "openai",
            "gemini",
        ],

    )

    assert request.request_id == "req-001"

    assert len(
        request.providers
    ) == 2



def test_response_normalization():

    normalizer = ResponseNormalizer()


    responses = [

        {
            "provider": "openai",
            "content": "Bullish",
            "extra": "data",
        },

        {
            "provider": "gemini",
            "content": "Neutral",
        },

    ]


    result = normalizer.normalize(
        responses
    )


    assert len(result) == 2

    assert result[0]["provider"] == "openai"

    assert "extra" not in result[0]



def test_agreement_evaluator():

    evaluator = AgreementEvaluator()


    score = evaluator.calculate(

        [

            {
                "provider": "claude",
                "content": "positive",
            }

        ]

    )


    assert isinstance(
        score,
        ConsensusScore,
    )


    assert score.agreement == 1.0



def test_consensus_engine_flow():

    engine = ConsensusEngine(

        normalizer=ResponseNormalizer(),

        evaluator=AgreementEvaluator(),

    )


    request = ConsensusRequest(

        request_id="runtime-001",

        query="Market direction",

    )


    response = engine.evaluate(

        request,

        [

            {
                "provider": "openai",

                "content": "Market rising",

            },

            {
                "provider": "claude",

                "content": "Market rising",

            },

        ],

    )


    assert response.request_id == "runtime-001"


    assert len(
        response.participating_providers
    ) == 2



def test_provider_weight_calculation():

    calculator = ProviderWeightCalculator()


    assert calculator.calculate(
        0.9
    ) == 0.9


    assert calculator.calculate(
        -1
    ) == 0.0


    assert calculator.calculate(
        2
    ) == 1.0



def test_confidence_model():

    confidence = ConfidenceScore(

        value=0.95,

        reasoning="High agreement",

    )


    assert confidence.is_high() is True