# Phase 6.15.5 Risk Core Upgrade

Status:
Planned

Phase:
6.15 Architecture Hardening


## Objective

Upgrade Risk Foundation into extensible Risk Core.


## Structure

src/lidoma_engines/risk/

    market.py
    portfolio.py
    exposure.py
    stress.py
    explainability.py


## Purpose


market.py

Market risk calculations.


portfolio.py

Portfolio level risk aggregation.


exposure.py

Exposure measurement.


stress.py

Scenario and stress evaluation.


explainability.py

Risk explanation output.


## Impact

No breaking changes.

Existing:

RiskEngine
RiskAssessment
RiskPolicy

remain compatible.


## Validation

python -m compileall src\lidoma_engines\risk

Risk Core API import test.