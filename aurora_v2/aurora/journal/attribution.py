"""Attribution of book changes: a flip is not the same event as a resize.

The engine already counts sign flips, but the book never separated them, so every
"changed" line looked alike. That matters for two reasons:

- cost: a flip closes one position and opens the opposite, so it pays the spread and
  commission twice. A resize pays once. Reporting them together understates the cost
  of the flips and overstates the cost of the resizes.
- diagnosis: a book that churns by resizing is drifting quietly; a book with many
  flips is fighting itself, and the two call for different responses.

The classification is by sign of the target weight, so it works for a long-only
equity book today and a long/short book later without changing the code.
"""
from dataclasses import dataclass
from typing import Dict, List, Sequence

ENTER, EXIT, INCREASE, DECREASE, FLIP, HOLD = (
    "enter", "exit", "increase", "decrease", "flip", "hold")

# a flip pays both sides: that is the entire point of counting it separately
SIDES = {ENTER: 1, EXIT: 1, INCREASE: 1, DECREASE: 1, FLIP: 2, HOLD: 0}


@dataclass(frozen=True)
class Change:
    symbol: str
    kind: str
    before: float
    after: float

    @property
    def delta(self) -> float:
        return self.after - self.before

    @property
    def cost_units(self) -> int:
        """How many half-spreads this change pays, in units of a normal trade."""
        return SIDES.get(self.kind, 1)

    def line(self) -> str:
        return f"{self.kind} {self.symbol} {self.before:+.2f} -> {self.after:+.2f}"


def classify(before: float, after: float, tol: float = 1e-12) -> str:
    # an identical weight is not a decrease: equality must be checked before direction
    if abs(after - before) <= tol:
        return HOLD
    if before == 0 and after == 0:
        return HOLD
    if before == 0:
        return ENTER
    if after == 0:
        return EXIT
    if (before > 0) != (after > 0):
        return FLIP
    return INCREASE if abs(after) > abs(before) else DECREASE


def events(current: Dict[str, float], target: Dict[str, float]) -> List[Change]:
    out: List[Change] = []
    for sym in sorted(set(current) | set(target)):
        before = current.get(sym, 0.0)
        after = target.get(sym, 0.0)
        kind = classify(before, after)
        if kind != HOLD:
            out.append(Change(sym, kind, before, after))
    return out


def summarise(changes: Sequence[Change]) -> Dict[str, int]:
    counts: Dict[str, int] = {k: 0 for k in (ENTER, EXIT, INCREASE, DECREASE, FLIP)}
    for c in changes:
        counts[c.kind] = counts.get(c.kind, 0) + 1
    return counts


def effective_cost_units(changes: Sequence[Change]) -> int:
    """Total half-spreads paid, where a flip counts twice."""
    return sum(c.cost_units for c in changes)


def describe(changes: Sequence[Change]) -> str:
    counts = summarise(changes)
    parts = [f"{k} {v}" for k, v in counts.items() if v]
    if not parts:
        return "no change"
    flips = counts.get(FLIP, 0)
    tail = " (flips pay both sides)" if flips else ""
    return ", ".join(parts) + f" · {effective_cost_units(changes)} cost units{tail}"
