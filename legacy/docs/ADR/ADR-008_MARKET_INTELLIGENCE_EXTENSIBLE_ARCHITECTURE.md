# ADR-008 Market Intelligence Extensible Architecture

Status:
ACCEPTED

Version:
LIDOMA Architecture Blueprint v3.1


## Decision

LIDOMA Financial Intelligence System shall use
a plugin-based extensible intelligence architecture.

External data sources, brokers, analysts,
AI models and strategies must never modify
the core decision architecture.


## Core Principle

Core Stability + Unlimited Extension


## Architecture Rule

External Source

        ↓

Adapter Layer

        ↓

Intelligence Layer

        ↓

Consensus Engine

        ↓

Decision Engine

        ↓

Risk Gate

        ↓

Execution Engine


## Supported External Categories


### Market Providers

- MT5 Brokers
- cTrader Brokers
- FIX API Providers
- Crypto Exchanges


### Technical Intelligence

- TradingView
- Pine Script
- TrendSpider
- Technical Analysts


### Fundamental Intelligence

- Forex Factory
- FRED
- CFTC CoT
- Macro Data Providers


### Alternative Intelligence

- ACCERN
- DataLoop
- News Providers


### Expert Intelligence

- Trader Profiles
- Trading Methodologies
- Expert Consensus


### Quant Intelligence

- Statistical Models
- Algorithmic Research
- Machine Learning Models


## Non Breaking Extension Rule

Adding new:

- Broker
- Website
- Expert
- AI Model
- Strategy
- Data Provider

must only create a new adapter/plugin.


## Trading System Rule

No direct trading execution.

Every trade must pass:

Market Analysis

↓

Consensus

↓

Decision

↓

Risk Approval

↓

Execution


## Governance

All modules require:

- Contract Validation
- Version Control
- Runtime Validation