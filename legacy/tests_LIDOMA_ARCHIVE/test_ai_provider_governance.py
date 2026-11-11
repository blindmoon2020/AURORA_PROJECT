from datetime import datetime, timezone

import pytest


from lidoma_finance.intelligence.ai.governance import (
    ProviderIdentity,
    ProviderCapability,
    ProviderHealth,
    ProviderVersion,
)


def test_provider_identity_creation():

    provider = ProviderIdentity(

        provider_id="openai",

        display_name="OpenAI",

        organization="OpenAI",

    )

    assert provider.provider_id == "openai"



def test_provider_identity_validation():

    with pytest.raises(ValueError):

        ProviderIdentity(

            provider_id="",

            display_name="OpenAI",

            organization="OpenAI",

        )



def test_provider_capability_creation():

    capability = ProviderCapability(

        provider_id="gemini",

        reasoning=True,

        research=True,

        coding=True,

        multimodal=True,

        realtime=True,

    )

    assert capability.multimodal is True



def test_provider_health_creation():

    health = ProviderHealth(

        provider_id="claude",

        available=True,

        latency_ms=120,

    )

    assert health.available is True



def test_provider_version_creation():

    version = ProviderVersion(

        provider_id="deepseek",

        provider_version="1.0",

        model_version="v3",

        schema_version="1",

    )

    assert version.model_version == "v3"