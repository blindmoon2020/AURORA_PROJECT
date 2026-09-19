# Phase 6.15.2 Shared Kernel Layer

Status:
Planned

Phase:
6.15 Architecture Hardening


## Objective

Create shared primitives used by all LIDOMA engines.


## Structure

src/lidoma_core/shared/

    __init__.py
    identifiers.py
    timestamps.py
    confidence.py
    scoring.py
    metadata.py
    provenance.py


## Purpose


identifiers.py

Common identifiers and validation.


timestamps.py

Unified timezone-aware timestamps.


confidence.py

Confidence representation.


scoring.py

Unified score normalization.


metadata.py

Shared metadata contract.


provenance.py

Source traceability support.


## Impact

No existing engine changes.

No domain breaking changes.


## Validation

python -m compileall src\lidoma_core\shared

Shared API import test.