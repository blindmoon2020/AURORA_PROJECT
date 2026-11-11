# ADR-006 — LIDOMA Evolution Foundation

## Status
Accepted for Phase 5.5.1.

## Context
LIDOMA already has a stable `lidoma_core` domain package and a root-level
engine blueprint (`01_DATA_ENGINE`, `03_INTELLIGENCE_ENGINE`,
`05_AI_ORCHESTRATION`, `07_RISK_ENGINE`, `11_PLUGIN_SYSTEM`, etc.).

Optional experts, AI vendors, websites, analytical methods and future
capabilities must not force changes to the stable domain core.

## Decision
Runtime extension contracts and registries live in the independent,
importable `src/lidoma_engines` package.

Root-level numbered engine directories remain architecture/workspace
boundaries. They must not be used as Python package names because names
beginning with digits are unsuitable import package identifiers.

`lidoma_core` MUST NOT import `lidoma_engines`.

Providers plug into LIDOMA via stable contracts and registry descriptors.
Domain mutation remains behind application/risk validation.

## Mandatory foundation categories
- Expert knowledge providers
- AI providers
- Market/news/research sources
- Analysis providers
- Strategy/risk/plugin providers
- Provenance records
- Capability registry

## Mandatory initial registry
Experts:
- علیرضا سلیمانی‌خواه (سولی)
- کوروش گرامی
- آیدین جبارپور

AI:
- OpenAI / ChatGPT
- Gemini
- Claude
- Grok
- DeepSeek

Sources:
- Forex Factory
- TradingView
- TrendSpider
- Accern
- Dataloop
- FXDyno
- Beaveron (historical/discontinued provenance retained)

Analysis:
- Advanced Price Action
- Smart Money
- Support / Resistance
- Fibonacci
- Fixed Range Volume Profile (POC, LVN, HVN)
- Supply / Demand
- Sentiment
- Fundamental analysis

## Consequences
New providers can be registered without rewriting the domain core.
Provider-specific APIs and credentials are deferred to adapters in later
phases. Persistence/distributed discovery is also deferred.
