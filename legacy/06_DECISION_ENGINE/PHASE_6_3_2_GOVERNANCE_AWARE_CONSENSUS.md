# LIDOMA Phase 6.3.2
## Governance-Aware Consensus and Deterministic Freshness Decay

Status: Implementation Candidate

Baseline:
- Phase 6.3.1 checkpoint: ce5e152
- Full regression baseline: 155 passing tests

## Purpose

Phase 6.3.2 integrates evidence freshness governance with the deterministic
consensus runtime without changing the behavior of legacy Phase 6, Phase 6.1,
or Phase 6.2 callers.

## Runtime

DecisionEvidence
-> Freshness Evaluation
-> Governance
-> Freshness Decay
-> Accepted Governed Evidence
-> Reliability Resolution
-> Correlation Clustering
-> Consensus
-> Decision Proposal
-> Future Risk Engine

Rejected evidence remains available in governance audit results but cannot
participate in consensus.

## Freshness Decay

FRESH:
factor = 1.0

STALE:
linear deterministic decay from 1.0 at stale_after toward 0.0 at
expire_after.

EXPIRED:
factor = 0.0 and REJECT.

FUTURE_DATED:
factor = 0.0 and REJECT.

## Weighting Order

Consensus raw weight is conceptually:

confidence
x resolved reliability
x configured evidence weight
x freshness factor

Correlation adjustment is applied after freshness adjustment.

This ordering prevents stale duplicated information from receiving full
influence before correlation control.

## Immutability

DecisionEvidence is never modified to apply freshness.

Freshness influence exists as external governance metadata.

This preserves the original evidence for provenance, replay, audit, and future
reliability calibration.

## Backward Compatibility

ConsensusEngine.evaluate() preserves Phase 6.2 behavior and assumes freshness
factor 1.0.

ConsensusEngine.evaluate_governed() is the new Phase 6.3.2 path.

DecisionEngine preserves:
- decide()
- decide_from_evidence()
- decide_from_consensus_evidence()

Phase 6.3.2 adds:
- decide_from_governed_evidence()

## Audit

Rejected evidence is not silently deleted.

EvidenceGovernanceResult retains accepted and rejected governed evidence,
freshness assessment, decay assessment, disposition, and reasons.

## Multi-Asset Requirement

No freshness or decay rule is hard-coded for cryptocurrency, forex, equities,
commodities, indices, ETFs, bonds, futures, options, or any other asset class.

Capability-specific policy is supported independently of asset identity.

## Trust Boundary

A Phase 6.3.2 Decision remains a Decision Proposal.

Evidence
-> Governance
-> Consensus
-> Decision Proposal
-> TRUST BOUNDARY
-> Future Risk Engine
-> Risk Approval or Rejection
-> Order Intent
-> Execution Engine

No expert, AI provider, website, analysis method, consensus result, or
DecisionEngine path may directly bypass future Risk Engine controls.