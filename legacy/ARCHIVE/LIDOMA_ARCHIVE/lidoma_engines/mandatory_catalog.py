from __future__ import annotations

from .contracts import ProviderDescriptor, ProviderKind, ProviderStatus
from .registry import CapabilityRegistry, RegistryEntry


def _entry(
    provider_id: str,
    name: str,
    kind: ProviderKind,
    capabilities: tuple[str, ...],
    *,
    aliases: tuple[str, ...] = (),
    status: ProviderStatus = ProviderStatus.ACTIVE,
    notes: str = "",
) -> RegistryEntry:
    return RegistryEntry(
        descriptor=ProviderDescriptor(
            provider_id=provider_id,
            name=name,
            kind=kind,
            capabilities=capabilities,
            status=status,
            mandatory=True,
        ),
        aliases=aliases,
        notes=notes,
    )


MANDATORY_ENTRIES: tuple[RegistryEntry, ...] = (
    _entry(
        "expert.alireza_solimankhah_soli",
        "علیرضا سلیمانی‌خواه",
        ProviderKind.EXPERT,
        (
            "technical_analysis",
            "price_action",
            "support_resistance",
            "market_education",
            "ai_in_finance_research",
        ),
        aliases=("سولی", "Soli", "Soli Trader"),
        notes="Public educational/research material must be provenance-tracked.",
    ),
    _entry(
        "expert.kourosh_gerami",
        "کوروش گرامی",
        ProviderKind.EXPERT,
        (
            "technical_analysis",
            "price_action",
            "fundamental_analysis",
            "valuation",
            "forex",
            "macro",
            "dollar_analysis",
            "budget_analysis",
        ),
    ),
    _entry(
        "expert.aidin_jabarpour",
        "آیدین جبارپور",
        ProviderKind.EXPERT,
        (
            "price_action",
            "supply_demand",
            "fibonacci",
            "multi_timeframe",
            "risk_management",
            "trading_psychology",
            "macro",
            "fundamental_analysis",
            "sentiment",
        ),
    ),

    _entry("ai.openai", "OpenAI / ChatGPT", ProviderKind.AI,
           ("reasoning", "research", "coding", "structured_extraction", "multimodal", "agents")),
    _entry("ai.gemini", "Google Gemini", ProviderKind.AI,
           ("reasoning", "research", "structured_extraction", "multimodal", "agents")),
    _entry("ai.claude", "Anthropic Claude", ProviderKind.AI,
           ("reasoning", "research", "coding", "structured_extraction", "agents")),
    _entry("ai.grok", "xAI Grok", ProviderKind.AI,
           ("reasoning", "research", "structured_extraction", "agents")),
    _entry("ai.deepseek", "DeepSeek", ProviderKind.AI,
           ("reasoning", "research", "coding", "structured_extraction")),

    _entry("source.forex_factory", "Forex Factory", ProviderKind.MARKET_SOURCE,
           ("economic_calendar", "macro_events", "actual_forecast_previous", "impact")),
    _entry("source.tradingview", "TradingView", ProviderKind.MARKET_SOURCE,
           ("multi_asset_charting", "technical_research", "market_reference")),
    _entry("source.trendspider", "TrendSpider", ProviderKind.MARKET_SOURCE,
           ("automated_technical_analysis", "support_resistance", "fibonacci", "backtesting", "ai_research")),
    _entry("source.accern", "Accern", ProviderKind.MARKET_SOURCE,
           ("financial_nlp", "event_intelligence", "alternative_data_research")),
    _entry("source.dataloop", "Dataloop", ProviderKind.PLUGIN,
           ("ai_data_stack", "data_orchestration", "model_pipeline")),
    _entry(
        "source.fxdyno",
        "FXDyno",
        ProviderKind.STRATEGY,
        ("ea_research", "gold_research", "mt4_research"),
        status=ProviderStatus.RESEARCH_ONLY,
        notes="Vendor claims require independent backtest/forward-test validation.",
    ),
    _entry(
        "source.beaveron",
        "Beaveron",
        ProviderKind.MARKET_SOURCE,
        ("historical_charting", "market_replay", "backtest_research"),
        status=ProviderStatus.DISCONTINUED,
        notes="Retained for provenance; successor adapter may be registered separately.",
    ),

    _entry("analysis.advanced_price_action", "Advanced Price Action", ProviderKind.ANALYSIS,
           ("market_structure", "swing_structure", "trend_range", "breakout_failure", "candle_context", "multi_timeframe")),
    _entry("analysis.smart_money", "Smart Money", ProviderKind.ANALYSIS,
           ("liquidity", "liquidity_sweep", "displacement", "structure_shift", "order_block", "fair_value_gap")),
    _entry("analysis.support_resistance", "Support / Resistance", ProviderKind.ANALYSIS,
           ("horizontal_zones", "role_reversal", "strength_scoring", "multi_timeframe")),
    _entry("analysis.fibonacci", "Fibonacci", ProviderKind.ANALYSIS,
           ("retracement", "extension", "configurable_anchors", "multi_timeframe", "confluence")),
    _entry("analysis.fixed_range_volume_profile", "Fixed Range Volume Profile", ProviderKind.ANALYSIS,
           ("poc", "lvn", "hvn", "volume_distribution", "value_area", "fixed_range")),
    _entry("analysis.supply_demand", "Supply / Demand", ProviderKind.ANALYSIS,
           ("supply_zones", "demand_zones", "multi_timeframe")),
    _entry("analysis.sentiment", "Sentiment Analysis", ProviderKind.ANALYSIS,
           ("news_sentiment", "market_sentiment", "confidence_scoring")),
    _entry("analysis.fundamental", "Fundamental Analysis", ProviderKind.ANALYSIS,
           ("financial_statements", "valuation", "macro_context")),
)


def build_mandatory_registry() -> CapabilityRegistry:
    """Return a fresh registry containing all mandatory Phase 5.5.1 entries."""
    return CapabilityRegistry(MANDATORY_ENTRIES)
