# Phase 6.15.3 Event Versioning Layer

Status:
Planned

Phase:
6.15 Architecture Hardening


## Objective

Add explicit event version management
before Phase 7.


## Structure

src/lidoma_core/events/versioning/

    __init__.py
    event_schema.py
    migration.py
    compatibility.py


## Purpose


event_schema.py

Define versioned event schema.


migration.py

Handle event schema migration.


compatibility.py

Validate event compatibility.


## Impact

No existing event breaking change.

Existing DomainEvent remains compatible.


## Validation

python -m compileall src\lidoma_core\events\versioning

Event version API import test.