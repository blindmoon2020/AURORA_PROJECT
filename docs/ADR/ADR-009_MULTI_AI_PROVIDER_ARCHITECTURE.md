# ADR-009 Multi AI Provider Architecture

Status:
ACCEPTED

Version:
LIDOMA Architecture Blueprint v3.2


## Decision

LIDOMA shall support unlimited AI providers
through a plugin based AI provider architecture.


## Core Rule

AI Models are replaceable intelligence providers.

The LIDOMA Core must never depend on
a single AI vendor.


## Supported AI Categories


### Reasoning Models

Examples:

- GPT
- Claude
- Gemini
- DeepSeek


### Real Time Intelligence

Examples:

- Grok
- Market AI Models


### Quant Intelligence

Examples:

- DeepSeek
- Custom Quant Models
- Local Models


### Research Intelligence

Examples:

- Gemini
- Claude


## AI Provider Flow


AI Provider

↓

AI Adapter

↓

AI Router

↓

AI Agent

↓

Consensus Engine

↓

Decision Engine


## AI Adapter Rule


Adding a new AI model requires only:

- New Adapter
- Capability Definition
- Confidence Profile


No Core Modification.


## AI Governance


Every AI output requires:

- Confidence Score
- Source Tracking
- Validation
- Consensus


## Trading Rule


No AI model can directly execute trades.


AI Output

↓

Consensus

↓

Risk Validation

↓

Execution


## Future Compatibility


Supports:

- New commercial AI models
- Open Source LLMs
- Local AI models
- Specialized Financial Models
- Custom Neural Networks