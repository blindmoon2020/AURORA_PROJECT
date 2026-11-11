# LIDOMA Phase 6.2 - Full Runtime Redesign V3

## Objective

Phase 6.2 introduces correlation-aware, reliability-aware consensus without
breaking Phase 6 or Phase 6.1.

## Stable migration rule

New capability must extend existing contracts rather than replace them.

The V3 package therefore preserves:

- DecisionEngine.decide()
- DecisionEngine.decide_from_evidence()
- EvidenceAggregator
- EvidenceAggregate
- DecisionTrace / ExplainabilityBuilder

and adds:

- DecisionEvidence.dependency_keys
- EvidenceCorrelationClusterer
- SourceReliabilityProfile
- ReliabilityResolver
- ConsensusEngine
- ConsensusResult
- DecisionPolicy.minimum_independent_clusters
- DecisionEngine.decide_from_consensus_evidence()

## Runtime flow

External Expert / AI / Source / Analysis
    -> normalized DecisionEvidence
    -> explicit dependency lineage
    -> transitive dependency clustering
    -> resolved source/capability reliability
    -> correlation-aware consensus weighting
    -> EvidenceAggregate
    -> DecisionPolicy
    -> Decision proposal
    -> future Risk Gate
    -> future Execution

## Correlation model

Correlation in Phase 6.2 means explicit evidence dependency, not Pearson
correlation.

The clusterer uses connected components over shared dependency keys.

Example:

A -> X
B -> X, Y
C -> Y

All three are one cluster.

## Cluster influence budget

A correlated cluster is not discarded.

Its total adjusted influence is capped at the strongest raw evidence member,
and all member weights are scaled proportionally.

This preserves internal disagreement while preventing repeated upstream
information from multiplying confidence.

## Reliability model

Reliability resolution order:

1. exact source + capability profile
2. source-wide profile
3. reliability already supplied by DecisionEvidence

This design is storage-agnostic. A future adapter can read reliability from
CapabilityRegistry, persistence, or realized-outcome calibration.

## Decision policy

Phase 6.2 adds minimum_independent_clusters.

This prevents three correlated copies of one event from satisfying a policy
that requires two independent confirmations.

## Backward compatibility

Phase 6 legacy score path remains intact.

Phase 6.1 evidence aggregation remains intact.

Phase 6.2 is additive and available through a separate method.

## Multi-asset requirement

No Phase 6.2 runtime rule is crypto-specific.

Tests cover forex, commodities, and equities.

## Explicit non-responsibilities

Phase 6.2 does not:

- call external AI providers
- scrape websites
- place orders
- mutate portfolio state
- size positions
- perform final risk approval
- calculate statistical correlation
- learn reliability from realized outcomes

These belong to later adapters and phases.
