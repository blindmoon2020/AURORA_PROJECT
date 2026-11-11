# ADR-007: Provider-Agnostic Decision Evidence Aggregation

Status: Accepted for Phase 6.1

## Context

LIDOMA must combine evidence from multiple experts, AI providers, market-data
sources, websites, and analysis methods without hard-coding any of those names
inside the Decision Engine.

Conflicting sources must remain visible and auditable. The system must also be
able to recommend NO_TRADE when evidence is weak or contradictory.

## Decision

Introduce normalized `DecisionEvidence`, deterministic `EvidenceAggregator`,
`EvidenceAggregate`, and `DecisionTrace`.

Decision Engine depends on those normalized contracts rather than named
providers.

Policy thresholds are injected through `DecisionPolicy`.

The legacy three-score `decide()` path remains temporarily for backward
compatibility. Evidence-first callers use `decide_from_evidence()`.

## Consequences

Positive:
- provider-independent Decision Engine
- deterministic aggregation
- explicit conflict measurement
- auditable evidence IDs and source IDs
- first-class NO_TRADE
- multi-asset-safe contracts
- future AI explanation can render facts without changing facts

Trade-offs:
- current aggregation formula is intentionally simple
- source reliability calibration is not solved in Phase 6.1
- correlation/dependency between evidence sources is not yet modeled
- institutional risk approval remains outside this phase

## Future work

- correlation-aware evidence weighting
- capability-specific policies
- temporal decay/freshness policies
- registry-backed reliability scoring
- AI consensus routing
- strategy DNA integration
- persistent audit store
- formal Risk Gate
