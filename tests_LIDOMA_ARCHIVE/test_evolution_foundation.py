from datetime import datetime, timezone

import pytest

from lidoma_engines import (
    CapabilityRegistry,
    ProvenanceRecord,
    ProviderDescriptor,
    ProviderKind,
    RegistryEntry,
    build_mandatory_registry,
)


def test_mandatory_registry_contains_required_experts_ai_sources_and_analysis() -> None:
    registry = build_mandatory_registry()

    required = {
        "expert.alireza_solimankhah_soli",
        "expert.kourosh_gerami",
        "expert.aidin_jabarpour",
        "ai.openai",
        "ai.gemini",
        "ai.claude",
        "ai.grok",
        "ai.deepseek",
        "source.forex_factory",
        "source.tradingview",
        "source.trendspider",
        "source.accern",
        "source.dataloop",
        "source.fxdyno",
        "source.beaveron",
        "analysis.advanced_price_action",
        "analysis.smart_money",
        "analysis.support_resistance",
        "analysis.fibonacci",
        "analysis.fixed_range_volume_profile",
    }

    assert all(registry.contains(item) for item in required)


def test_fixed_range_volume_profile_exposes_required_nodes() -> None:
    registry = build_mandatory_registry()
    capabilities = set(
        registry.get("analysis.fixed_range_volume_profile").descriptor.capabilities
    )
    assert {"poc", "lvn", "hvn"} <= capabilities


def test_registry_is_extensible_without_modifying_mandatory_catalog() -> None:
    registry = build_mandatory_registry()
    initial_count = len(registry)

    registry.register(
        RegistryEntry(
            descriptor=ProviderDescriptor(
                provider_id="analysis.future_method",
                name="Future Method",
                kind=ProviderKind.ANALYSIS,
                capabilities=("future_capability",),
            )
        )
    )

    assert len(registry) == initial_count + 1
    assert registry.contains("analysis.future_method")


def test_registry_rejects_duplicate_provider_by_default() -> None:
    registry = CapabilityRegistry()
    entry = RegistryEntry(
        descriptor=ProviderDescriptor(
            provider_id="ai.example",
            name="Example AI",
            kind=ProviderKind.AI,
        )
    )
    registry.register(entry)

    with pytest.raises(ValueError):
        registry.register(entry)


def test_provenance_requires_timezone_aware_capture_time() -> None:
    with pytest.raises(ValueError):
        ProvenanceRecord(
            source_id="source.test",
            source_type="market_source",
            captured_at=datetime(2026, 1, 1),
        )

    record = ProvenanceRecord(
        source_id="source.test",
        source_type="market_source",
        captured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        confidence=0.8,
    )
    assert record.confidence == 0.8


def test_core_has_no_dependency_on_evolution_package() -> None:
    import importlib.util

    if importlib.util.find_spec("lidoma_core") is None:
        pytest.skip("lidoma_core is not present in this isolated package test environment")

    import lidoma_core
    assert "lidoma_engines" not in getattr(lidoma_core, "__dict__", {})
