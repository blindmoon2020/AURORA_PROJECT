# ADR-008: Correlation-Aware Consensus and Reliability

Status: Accepted for Phase 6.2 V3

## Context

LIDOMA can receive evidence from multiple experts, AI systems, websites, market
sources, and analysis methods.

Multiple outputs may depend on one upstream event. Counting each output as an
independent vote can create false confidence.

At the same time, source reliability must remain replaceable and must not be
hard-coded into Decision Engine.

## Decision

Adopt explicit dependency lineage and correlation-aware consensus.

The following contracts are introduced or evolved:

- DecisionEvidence.dependency_keys
- EvidenceCluster
- EvidenceCorrelationClusterer
- SourceReliabilityProfile
- ReliabilityResolver
- InMemoryReliabilityResolver
- ConsensusResult
- ConsensusEngine
- DecisionPolicy.minimum_independent_clusters
- DecisionEngine.decide_from_consensus_evidence

## Dependency clustering

Evidence items are nodes.

A shared dependency key creates a graph connection.

Clusters are transitive connected components.

Provider identity alone is not treated as correlation.

## Influence rule

Independent one-item clusters retain full resolved weight.

Correlated clusters receive a total influence budget equal to the strongest
member's raw resolved weight.

Member weights are proportionally scaled into the cluster budget.

## Reliability boundary

ConsensusEngine depends on a ReliabilityResolver protocol.

This prevents storage, registry, model vendor, and expert identity concerns from
entering Decision Engine.

## Compatibility

Existing Phase 6 and Phase 6.1 APIs remain available.

Phase 6.2 is additive.

## Consequences

Positive:
- prevents duplicate-confirmation inflation
- supports transitive dependencies
- keeps provider identities outside Decision Engine
- supports capability-specific reliability
- remains deterministic and auditable
- supports multi-asset use

Trade-offs:
- dependency keys must currently be supplied upstream
- reliability calibration is deferred
- semantic duplicate detection is deferred
- statistical correlation is deferred
