from lidoma_finance.intelligence.ai.governance import (
    ProviderIdentity,
    ProviderCapability,
    ProviderHealth,
    ProviderVersion,
    EnvironmentCredentialResolver,
    ProviderRegistry,
    ProviderHealthMonitor,
    ProviderVersionValidator,
)


def test_provider_registry_runtime_flow():

    registry = ProviderRegistry()

    provider = ProviderIdentity(
        provider_id="gemini",
        display_name="Gemini",
        organization="Google",
    )

    registry.register(provider)

    assert registry.exists(
        "gemini"
    )

    assert registry.get(
        "gemini"
    ).provider_id == "gemini"



def test_health_monitor_runtime_flow():

    monitor = ProviderHealthMonitor()

    health = monitor.create_status(

        provider_id="openai",

        available=True,

        latency_ms=150,

    )

    assert isinstance(
        health,
        ProviderHealth
    )

    assert health.available is True



def test_version_validator_runtime_flow():

    validator = ProviderVersionValidator()

    version = ProviderVersion(

        provider_id="claude",

        provider_version="1.0",

        model_version="sonnet",

        schema_version="1",

    )

    assert validator.validate(
        version
    ) is True



def test_capability_contract_runtime():

    capability = ProviderCapability(

        provider_id="deepseek",

        reasoning=True,

        research=True,

        coding=True,

        multimodal=False,

        realtime=False,

    )

    assert capability.provider_id == "deepseek"



def test_credential_resolver_contract():

    resolver = EnvironmentCredentialResolver()

    assert hasattr(
        resolver,
        "resolve"
    )