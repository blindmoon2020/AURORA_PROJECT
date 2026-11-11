# Phase 6.1 - Evidence Aggregation and Explainability

## Purpose

Phase 6.1 introduces a provider-agnostic evidence layer between intelligence
sources and the Decision Engine.

The Decision Engine must not know the names of experts, AI providers, websites,
brokers, strategies, or asset classes. Those systems must first produce
normalized evidence.

## Runtime flow

External Expert / AI / Site / Analysis Method
-> Intelligence Layer
-> Normalized DecisionEvidence
-> EvidenceAggregator
-> EvidenceAggregate
-> ExplainabilityBuilder
-> DecisionEngine
-> Decision proposal
-> Future Risk Gate
-> Future Execution workflow

## Core rules

1. A decision is a proposal, not an order.
2. The engine does not mutate portfolio or order state.
3. Conflicting evidence is retained and measured instead of overwritten.
4. NO_TRADE is a first-class outcome.
5. Every evidence item keeps a source identifier and may carry provenance.
6. Aggregation is deterministic and reproducible.
7. Provider-specific logic stays outside the Decision Engine.
8. Multi-asset context is explicit and no asset class is privileged.
9. Thresholds are policy objects, not hidden constants.
10. Explainability facts are generated deterministically before any future LLM
    rendering.

## Aggregation model

Each evidence item has:

- confidence
- source reliability
- policy weight
- direction
- source_id
- capability
- reason
- optional provenance

Effective weight:

confidence * reliability * policy_weight

Directional score:

(bullish_weight - bearish_weight) /
(bullish_weight + bearish_weight)

The score is in [-1, 1].

Conflict ratio is maximal when bullish and bearish directional evidence have
equal effective weight. Confidence is reduced by conflict and by the amount of
non-directional evidence.

These formulas are foundation rules for Phase 6.1, not a claim that they are a
complete institutional risk or alpha model.

## Boundary with Risk Engine

RiskScore from the original Phase 6 foundation remains backward compatible but
must not be confused with the future institutional Risk Engine.

The future Risk Engine owns, among other things:

- exposure limits
- leverage limits
- concentration
- liquidity risk
- position sizing
- drawdown constraints
- portfolio-level risk
- broker/account constraints

Decision Engine only proposes.
