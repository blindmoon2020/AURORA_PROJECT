"""Strategy DNA: a strategy is data, not code.

A DNA file names a strategy type, gives its parameters, and carries its own risk
limits. Adding a variant means writing a JSON file, not editing the engine.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from ..risk.engine import RiskLimits
from .base import Strategy
from .ema_cross import STRATEGY_TYPES

REQUIRED_KEYS = ("name", "symbol", "type", "params", "risk")
AUTHORED_BY = "human"


class DnaError(ValueError):
    """Raised when a DNA file cannot be turned into a working strategy."""


@dataclass(frozen=True)
class StrategyDna:
    name: str
    symbol: str
    type: str
    params: Dict[str, Any]
    risk: RiskLimits
    source: Optional[str] = None
    notes: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def build(self) -> Strategy:
        factory = STRATEGY_TYPES.get(self.type)
        if factory is None:
            raise DnaError(
                f"unknown strategy type {self.type!r}; known: {sorted(STRATEGY_TYPES)}"
            )
        try:
            return factory(name=self.name, **self.params)
        except (TypeError, ValueError) as exc:
            raise DnaError(f"strategy {self.name!r} has invalid params: {exc}") from exc


def parse_dna(raw: Dict[str, Any], source: Optional[str] = None) -> StrategyDna:
    if not isinstance(raw, dict):
        raise DnaError(f"{source or 'dna'}: expected a JSON object")

    missing = [k for k in REQUIRED_KEYS if k not in raw]
    if missing:
        raise DnaError(f"{source or 'dna'}: missing required keys {missing}")

    risk_raw = raw["risk"]
    if not isinstance(risk_raw, dict):
        raise DnaError(f"{source or 'dna'}: 'risk' must be an object")
    known_risk = set(RiskLimits.__dataclass_fields__)
    unknown = set(risk_raw) - known_risk
    if unknown:
        raise DnaError(f"{source or 'dna'}: unknown risk keys {sorted(unknown)}")
    try:
        risk = RiskLimits(**risk_raw)
        risk.validate()
    except (TypeError, ValueError) as exc:
        raise DnaError(f"{source or 'dna'}: invalid risk block: {exc}") from exc

    name = raw["name"]
    if not isinstance(name, str) or not name.strip():
        raise DnaError(f"{source or 'dna'}: 'name' must be a non-empty string")
    symbol = raw["symbol"]
    if not isinstance(symbol, str) or not symbol.strip():
        raise DnaError(f"{source or 'dna'}: 'symbol' must be a non-empty string")
    params = raw["params"]
    if not isinstance(params, dict):
        raise DnaError(f"{source or 'dna'}: 'params' must be an object")

    dna = StrategyDna(
        name=name,
        symbol=symbol,
        type=str(raw["type"]),
        params=params,
        risk=risk,
        source=source,
        notes=str(raw.get("notes", "")),
        extra={k: v for k, v in raw.items() if k not in REQUIRED_KEYS and k not in ("notes",)},
    )
    dna.build()  # fail here, not three layers later
    return dna


def load_dna(path: str | Path) -> StrategyDna:
    p = Path(path)
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DnaError(f"dna file not found: {p}") from exc
    except json.JSONDecodeError as exc:
        raise DnaError(f"{p}: invalid JSON ({exc.msg} at line {exc.lineno})") from exc
    return parse_dna(raw, source=str(p))
