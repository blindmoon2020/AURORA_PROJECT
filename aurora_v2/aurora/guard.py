"""The bridge between a paper decision and a real broker that has no API.

Mofid gives no key, only a web page. So execution is a human copying ticket lines
and pasting back a fill export. The bridge does the three things a human cannot do
reliably at 9am: turn targets into sized, expiring tickets; refuse targets that
break the risk budget; and fold the returned fills back into the book so the
record stays continuous.

Nothing here places an order. It prepares instructions and reads results.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from aurora.execution.manual import (FillRecord, ManualExecutionError, OrderTicket,
                                     ticket)
from aurora.core.types import Side


@dataclass(frozen=True)
class GuardLimits:
    max_weight: float = 0.15          # per name
    max_gross: float = 1.00           # fully invested is the ceiling, not 1.5
    max_names: int = 20
    min_trade_weight: float = 0.01    # ignore dust that costs more than it moves


@dataclass
class GuardResult:
    allowed: Dict[str, float]
    blocked: List[tuple]              # (symbol, weight, reason)
    notes: List[str]

    @property
    def blocked_symbols(self) -> List[str]:
        return [s for s, _, _ in self.blocked]


def apply_limits(targets: Dict[str, float], limits: GuardLimits,
                 risk_off: bool = False) -> GuardResult:
    """Trim targets to the budget before they become money.

    Order is deliberate: risk-off first (nothing new), then dust, then the name
    cap, then the count, then gross. Each step can only reduce exposure.
    """
    allowed: Dict[str, float] = {}
    blocked: List[tuple] = []
    notes: List[str] = []

    if risk_off:
        return GuardResult({}, [(s, w, "risk-off: no new exposure") for s, w in targets.items()],
                           ["risk-off active: book held, no new entries"])

    for sym, w in targets.items():
        if w <= 0:
            continue
        if w < limits.min_trade_weight:
            blocked.append((sym, w, "below minimum trade size"))
            continue
        if w > limits.max_weight + 1e-12:
            notes.append(f"{sym} trimmed {w:.2%} -> {limits.max_weight:.2%} (name cap)")
            w = limits.max_weight
        allowed[sym] = w

    if len(allowed) > limits.max_names:
        keep = sorted(allowed.items(), key=lambda kv: -kv[1])[:limits.max_names]
        for sym, w in allowed.items():
            if sym not in dict(keep):
                blocked.append((sym, w, "name count limit"))
        allowed = dict(keep)
        notes.append(f"kept the {limits.max_names} largest targets")

    gross = sum(allowed.values())
    if gross > limits.max_gross + 1e-12:
        scale = limits.max_gross / gross
        allowed = {s: w * scale for s, w in allowed.items()}
        notes.append(f"gross {gross:.2f} scaled to {limits.max_gross:.2f}")
    return GuardResult(allowed, blocked, notes)
