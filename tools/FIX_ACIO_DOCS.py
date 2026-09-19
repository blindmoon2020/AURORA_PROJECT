from pathlib import Path

base = Path("docs/AURORA_ACIO_v1_2")

files = {
"AURORA_ACIO_ARCHITECTURE_MASTER_REVISION_v1.2.md": """
# AURORA ACIO Architecture Master Revision v1.2

## Purpose

Institutional architecture baseline for AURORA.

## Integrated Improvements

- AI Governance Upgrade
- Data Standardization Layer
- Low Latency Execution Architecture
- Institutional Risk Framework
- Quant Validation Framework

## Architecture Direction

AURORA continues as an independent financial intelligence platform.
""",

"AURORA_PHASE20_EXECUTION_GOVERNANCE.md": """
# PHASE20 Execution Governance

## Rules

- Architecture first
- Validation before integration
- Git checkpoint every milestone
- No undocumented changes

## Phase Gates

Design -> Implement -> Test -> Validate -> Commit
""",

"AURORA_ARCHITECTURE_CONSTITUTION.md": """
# AURORA Architecture Constitution v1.2

Status: ACTIVE

## Core Principles

- Domain independence
- Zero dependency on legacy systems
- Modular architecture
- Event driven design
- Governance controlled evolution

## Layer Rules

- Core is immutable foundation
- AI cannot directly execute trades
- Decision layer validates intelligence
- Risk layer controls exposure
- Execution layer performs approved actions

## Change Control

All architecture changes require ADR approval.
"""
}


for name, content in files.items():
    (base / name).write_text(content.strip()+"\n", encoding="utf-8")


architecture = {
"AI_GOVERNANCE_LAYER.md": """
# AI Governance Layer

## Rules

- Multi agent intelligence
- Model routing
- Human approval boundary
- No direct execution authority
""",

"INSTITUTIONAL_RISK_FRAMEWORK.md": """
# Institutional Risk Framework

## Components

- Exposure management
- Stress testing
- Scenario analysis
- Portfolio risk control
""",

"LOW_LATENCY_EXECUTION_ARCHITECTURE.md": """
# Low Latency Execution Architecture

AI Decision

-> Decision Gate

-> Risk Gate

-> Execution Core

-> Broker Adapter
""",

"PRODUCTION_ALIGNMENT_MATRIX.md": """
# Production Alignment Matrix

Modules tracked by:

- Designed
- Implemented
- Tested
- Production Ready
""",

"QUANT_VALIDATION_FRAMEWORK.md": """
# Quant Validation Framework

Research

-> Backtest

-> Walk Forward

-> Paper Trading

-> Validation
"""
}


for name, content in architecture.items():
    (base / "architecture" / name).write_text(content.strip()+"\n", encoding="utf-8")