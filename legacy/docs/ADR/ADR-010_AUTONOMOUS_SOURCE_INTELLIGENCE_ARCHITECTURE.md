# ADR-010 Autonomous Source Intelligence Architecture

Status:
ACCEPTED

Version:
LIDOMA Architecture Blueprint v3.4


## Decision

LIDOMA shall use an autonomous source intelligence
architecture.

Manual input is restricted only to source registration.

No manual financial data entry is allowed.


## Manual Input Policy

Allowed:

- Register website
- Register API
- Register Broker
- Register Analyst
- Register Research Source
- Register AI Provider
- Register Dataset


Not Allowed:

- Manual price input
- Manual signal input
- Manual market analysis
- Manual trade decision


## Source Lifecycle


Source Registration

↓

Source Discovery

↓

Source Verification

↓

Data Extraction

↓

Data Normalization

↓

Knowledge Storage

↓

AI Analysis

↓

Consensus Engine


## Source Registry

Every source must contain:

- Identity
- Category
- Access Method
- Reliability Score
- Validation Status
- Provenance


## Supported Source Types


Market:

- Brokers
- Exchanges
- Data Providers


Technical:

- TradingView
- TrendSpider
- Expert Analysts


Fundamental:

- Forex Factory
- FRED
- CFTC


Alternative:

- News
- Social Data
- Research


AI:

- GPT
- Claude
- Gemini
- Grok
- DeepSeek
- Future Models


## Source Governance Rules


1. Sources cannot directly execute decisions.

2. Every data point must preserve provenance.

3. Every source requires validation.

4. New sources must be added through adapters.

5. Core architecture must never change for new sources.


## Data Intelligence Flow


External Source

↓

Collector

↓

Validator

↓

Normalizer

↓

Knowledge Graph

↓

AI Intelligence

↓

Decision Engine