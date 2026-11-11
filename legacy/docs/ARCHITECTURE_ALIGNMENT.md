# LIDOMA Architecture Alignment

Version: 1.0

Status: Accepted


## Purpose

This document defines the architectural principles adopted by LIDOMA.

The purpose is to preserve a stable financial domain core while adopting
reliability, governance and audit principles inspired by LUNA architecture.


# Core Principles


## Provider Neutral Core

LIDOMA Core must never directly depend on:

- Exchange SDKs
- Broker SDKs
- AI providers
- External APIs
- Strategy implementations


External systems must connect through adapters.


## Domain Stability

The following are canonical domain objects:

- Asset
- Instrument
- Market
- Position
- Order


New capabilities must extend the domain without breaking existing contracts.


# Adopted Architectural Improvements


## Event Driven Foundation

Future events must support:

- event_id
- schema_version
- timestamp
- source
- correlation_id
- replay capability


## Risk Governance

Trading decisions must follow:

Decision

↓

Risk Validation

↓

Execution


No execution path can bypass risk controls.


## Auditability

Important decisions must be traceable.

Future audit records should contain:

- decision source
- strategy version
- risk result
- execution result
- timestamps


## Session Intelligence

Trading sessions are first-class domain concepts.

Future improvements:

- timezone handling
- DST support
- session overlap analysis


## Backtest Compatibility

Live trading and backtesting must share:

- domain models
- events
- lifecycle rules


# Layer Boundaries


## Core Layer

Contains:

- Entities
- Value Objects
- Domain Rules


Must not contain:

- Network calls
- Broker logic
- AI execution


## Adapter Layer

Responsible for:

- Exchanges
- Brokers
- External providers


## Intelligence Layer

Responsible for:

- AI analysis
- Research
- Decision support


AI does not have direct execution authority.


# Roadmap Alignment


Completed:

- Asset
- Instrument
- Market
- TradingSession
- TradingRules
- Position
- Currency


Next:

- Account
- Portfolio
- Balance


Future:

- Event Spine
- Audit Journal
- Risk Engine
- Execution Layer
- AI Orchestration


# Non Negotiable Rules


1. Core remains provider neutral.

2. No direct AI trading authority.

3. Risk validation before execution.

4. Domain changes require tests.

5. Breaking changes require explicit versioning.

6. Important architectural decisions must be documented.


# Final Decision

LIDOMA adopts reliability and governance principles from LUNA
while maintaining its own independent domain architecture.

The Core domain remains the single source of truth.