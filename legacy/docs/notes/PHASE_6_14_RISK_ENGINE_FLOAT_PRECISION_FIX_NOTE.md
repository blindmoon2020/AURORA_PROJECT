# Phase 6.14 Risk Engine Float Precision Fix Note

Status:
Fixed


Date:
2026-09-10


## Issue

Risk Engine assessment score generated floating point precision mismatch.

Example:

Expected:

0.3


Actual:

0.30000000000000004


## Affected Component

src/lidoma_engines/risk/engine.py


## Root Cause

Python floating point arithmetic can create
binary precision artifacts during average calculations.


Example:

(0.4 + 0.2) / 2

can produce:

0.30000000000000004


## Decision

Risk score output must be normalized before
creating RiskAssessment.


## Fix Strategy

Apply deterministic rounding to calculated
risk score.


## Architectural Impact

No changes to:

- Domain contracts
- Event contracts
- Risk Assessment model
- Decision Engine
- Evolution Layer


## Validation

Required:

python -m compileall src\lidoma_engines\risk

pytest -q tests\test_risk_foundation.py

pytest -q


Expected:

All tests passing.


## Phase

Phase 6.14 Risk Foundation Hardening