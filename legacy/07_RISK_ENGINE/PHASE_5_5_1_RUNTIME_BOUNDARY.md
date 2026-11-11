# Phase 5.5.1 Runtime Boundary

This root-level engine directory is part of LIDOMA's architecture map.

Runtime Python contracts for Phase 5.5.1 live in:

`src/lidoma_engines`

This avoids making the numbered workspace directory itself a Python
package while preserving the existing LIDOMA engine blueprint.

Rule: this engine may depend on stable contracts, but `lidoma_core`
must never depend on this engine.
