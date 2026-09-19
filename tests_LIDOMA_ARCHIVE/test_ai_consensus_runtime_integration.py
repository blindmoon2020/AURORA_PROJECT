from lidoma_finance.intelligence.consensus import (
    ConsensusEngine,
    ConsensusRequest,
    ResponseNormalizer,
    AgreementEvaluator,
    ProviderWeightCalculator,
    ConfidenceScore,
)


def create_runtime_engine():

    return ConsensusEngine(

        normalizer=ResponseNormalizer(),

        evaluator=AgreementEvaluator(),

    )


def test_multi_provider_consensus_flow():

    engine = create_runtime_engine()


    request = ConsensusRequest(

        request_id="integration-001",

        query="BTC market trend",

        providers=[

            "openai",

            "gemini",

            "claude",

        ],

    )


    responses = [

        {
            "provider": "openai",

            "content": "Bullish market",

        },

        {
            "provider": "gemini",

            "content": "Bullish market",

        },

        {
            "provider": "claude",

            "content": "Bullish market",

        },

    ]


    result = engine.evaluate(

        request,

        responses,

    )


    assert result.request_id == "integration-001"

    assert len(
        result.participating_providers
    ) == 3



def test_provider_failure_tolerance():

    engine = create_runtime_engine()


    request = ConsensusRequest(

        request_id="failure-001",

        query="Market analysis",

    )


    responses = [

        {
            "provider": "openai",

            "content": "Positive",

        },

        {
            "provider": "gemini",

        },

        {
            "provider": "claude",

            "content": "Positive",

        },

    ]


    result = engine.evaluate(

        request,

        responses,

    )


    assert result.request_id == "failure-001"

    assert len(
        result.participating_providers
    ) == 3



def test_provider_weight_pipeline():

    calculator = ProviderWeightCalculator()


    weights = [

        calculator.calculate(
            0.95
        ),

        calculator.calculate(
            0.80
        ),

        calculator.calculate(
            0.60
        ),

    ]


    assert weights == [

        0.95,

        0.80,

        0.60,

    ]



def test_confidence_pipeline():

    confidence = ConfidenceScore(

        value=0.90,

        reasoning="High provider agreement",

    )


    assert confidence.value > 0.8

    assert confidence.is_high()



def test_empty_response_handling():

    engine = create_runtime_engine()


    request = ConsensusRequest(

        request_id="empty-001",

        query="test",

    )


    result = engine.evaluate(

        request,

        [],

    )


    assert result.request_id == "empty-001"

    assert result.final_answer == ""