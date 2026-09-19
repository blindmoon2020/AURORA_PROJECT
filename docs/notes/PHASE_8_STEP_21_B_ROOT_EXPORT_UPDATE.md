# PHASE 8 — STEP 21-B
# Expert Intelligence Domain Contracts
# Stage 3 — Root Export Update


## Status

Completed


## Objective

Expose all Expert Intelligence domain contracts
through the experts package root export.

The root package must provide a stable public API
for external modules.


---

# Updated Package

Path:

src/lidoma_finance/intelligence/experts/__init__.py


---

# Exported Components


## Contract Layer

```python
ExpertIntelligenceContract
ExpertIdentity
ExpertProfile
ExpertReliability
ExpertRequest
from lidoma_finance.intelligence.experts import (

    ExpertIntelligenceContract,

    ExpertIdentity,

    ExpertProfile,

    ExpertReliability,

    ExpertRequest,

)