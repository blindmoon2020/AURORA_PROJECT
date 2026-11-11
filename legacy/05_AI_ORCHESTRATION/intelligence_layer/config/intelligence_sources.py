from registry.source_registry import SourceRegistry


def build_intelligence_registry():

    registry = SourceRegistry()


    # Technical Intelligence

    registry.register(
        name="TRENDSPIDER",
        category="TECHNICAL",
        weight=25
    )


    # Quant Validation

    registry.register(
        name="DALOOP",
        category="QUANT_VALIDATION",
        weight=20
    )


    # Sentiment / NLP

    registry.register(
        name="ACCERN",
        category="SENTIMENT",
        weight=20
    )


    # External Signal

    registry.register(
        name="FXDYNO",
        category="SIGNAL_PROVIDER",
        weight=10
    )


    # Fundamental

    registry.register(
        name="FOREX_FACTORY",
        category="ECONOMIC_NEWS",
        weight=15
    )


    # Macro

    registry.register(
        name="BOND_YIELD_ENGINE",
        category="MACRO",
        weight=10
    )


    registry.register(
        name="DXY_ENGINE",
        category="MACRO",
        weight=10
    )


    registry.register(
        name="GOLD_FLOW_ENGINE",
        category="COMMODITY_MACRO",
        weight=10
    )


    return registry