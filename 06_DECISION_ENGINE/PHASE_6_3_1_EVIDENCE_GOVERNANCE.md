# LIDOMA Phase 6.3.1
## Evidence Freshness and Governance Foundation

Status: Implementation Candidate

Baseline:
- Phase 6.2 checkpoint: d1ee6aa
- Full regression baseline: 140 passing tests

---

## 1. Purpose

Phase 6.3 introduces governance controls between normalized evidence ingestion
and consensus-based decisioning.

Phase 6.3.1 focuses exclusively on deterministic evidence freshness and
acceptance governance.

This phase does not modify the Phase 6.2 consensus runtime.

---

## 2. Architecture

External Expert / AI / Website / Analysis Method

-> Source Adapter

-> DecisionEvidence

-> EvidenceFreshnessEvaluator

-> EvidenceGovernanceEngine

-> Governed Evidence Set

-> Future Phase 6.3.2 Consensus Integration

-> Decision Proposal

-> Future Risk Engine

---

## 3. Core Principles

### Provider agnostic

Freshness policy cannot contain hard-coded AI vendors, experts, brokers,
websites, or named strategies.

### Capability aware

Different analytical capabilities may require different freshness windows.

Examples include:

- market.microstructure
- technical.structure
- sentiment
- macro.central_bank
- fundamental.earnings

These are capabilities, not provider identities.

### Deterministic

Given identical evidence, policy, and evaluation timestamp, the freshness
assessment must be reproducible.

### Timezone safe

All timestamps used for evaluation must be timezone-aware.

### Future timestamp protection

Evidence whose timestamp exceeds the configured future clock-skew allowance
is rejected.

### No silent evidence deletion

Rejected evidence remains represented in EvidenceGovernanceResult with an
explicit reason.

### Multi-asset

No asset class receives hard-coded decision behavior.

---

## 4. Freshness States

FRESH

Evidence age is below the configured stale threshold.

STALE

Evidence is older than the freshness threshold but has not reached expiration.

STALE evidence remains accepted with an explicit warning in Phase 6.3.1.

EXPIRED

Evidence age exceeds the expiration policy and is rejected before consensus.

FUTURE_DATED

Evidence timestamp exceeds the permitted clock skew and is rejected.

---

## 5. Governance Dispositions

ACCEPT

Evidence passed governance normally.

ACCEPT_WITH_WARNING

Evidence remains usable but contains a governance warning.

REJECT

Evidence must not participate in future consensus weighting.

---

## 6. Explicit Non-Responsibilities

Phase 6.3.1 does not:

- change ConsensusEngine
- change DecisionEngine
- modify portfolio state
- create orders
- execute trades
- size positions
- perform institutional risk approval
- call external AI providers
- call external websites
- infer source reliability
- apply time-decay weighting

---

## 7. Planned Phase 6.3 Evolution

Phase 6.3.2:
- integrate governance with ConsensusEngine
- ensure rejected evidence cannot influence consensus
- preserve rejected evidence for audit
- deterministic freshness decay for stale evidence

Phase 6.3.3:
- persistent reliability calibration
- source/capability reliability history
- outcome-based reliability updates

Phase 6.3.4:
- semantic duplicate evidence controls
- stronger dependency identity
- duplicate/near-duplicate evidence detection

Phase 6.3.5:
- evidence version identity
- provenance hardening
- governance audit records
- capability grouping and policy registry integration

---

## 8. Safety Boundary

Evidence Governance produces governed evidence.

It does not produce an executable order.

The intended long-term boundary remains:

Evidence
-> Governance
-> Consensus
-> Decision Proposal
-> Risk Engine
-> Risk Approval
-> Order Intent
-> Execution Engine

No AI provider, expert, website, analysis method, or consensus result may
directly bypass Risk Engine controls.