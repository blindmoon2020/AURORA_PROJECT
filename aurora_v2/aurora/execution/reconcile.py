"""Reconciliation: what the broker says we hold versus what we think we hold.

Gemini's criticism of manual execution was mostly right, but it missed the failure that
actually costs money first. Manual tickets create a gap between the book and the broker,
and that gap is where phantom positions live: a ticket filled twice, a fill typed into the
wrong symbol, a cancelled order the book still believes in. Every institution runs a
reconciliation gate before trading; a manual process without one is not a manual process,
it is an unverified one.

Tolerances are explicit and small on purpose. A tolerance that can hide one unit can hide
a hundred, and the person setting it will be the same person who benefits.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

UNIT_TOLERANCE = 1e-6
CASH_TOLERANCE = 0.01


@dataclass(frozen=True)
class Break:
    kind: str            # missing | phantom | size | cash
    symbol: str
    expected: float
    actual: float

    def line(self) -> str:
        return f"{self.kind}: {self.symbol} انتظار {self.expected:,.4f} · واقعی {self.actual:,.4f}"


@dataclass
class Reconciliation:
    breaks: List[Break] = field(default_factory=list)
    checked: int = 0

    @property
    def clean(self) -> bool:
        return not self.breaks

    @property
    def blocks_trading(self) -> bool:
        """Any break blocks the session. A partial match is not a permission to trade."""
        return bool(self.breaks)

    def summary(self) -> str:
        if self.clean:
            return f"تطبیق سالم: {self.checked} پوزیشن و نقد بررسی شد"
        kinds = {}
        for b in self.breaks:
            kinds[b.kind] = kinds.get(b.kind, 0) + 1
        return ("تطبیق ناموفق: " +
                "، ".join(f"{k}={v}" for k, v in sorted(kinds.items())))


def reconcile(expected: Dict[str, float], actual: Dict[str, float],
              cash_expected: Optional[float] = None, cash_actual: Optional[float] = None,
              unit_tolerance: float = UNIT_TOLERANCE,
              cash_tolerance: float = CASH_TOLERANCE) -> Reconciliation:
    """Compare the internal book with the broker's statement, position by position."""
    rep = Reconciliation()
    symbols = set(expected) | set(actual)
    for sym in sorted(symbols):
        want = float(expected.get(sym, 0.0))
        have = float(actual.get(sym, 0.0))
        rep.checked += 1
        if abs(want) > unit_tolerance and abs(have) <= unit_tolerance:
            rep.breaks.append(Break("missing", sym, want, have))
        elif abs(have) > unit_tolerance and abs(want) <= unit_tolerance:
            rep.breaks.append(Break("phantom", sym, want, have))
        elif abs(want - have) > unit_tolerance:
            rep.breaks.append(Break("size", sym, want, have))
    if cash_expected is not None and cash_actual is not None:
        rep.checked += 1
        if abs(cash_expected - cash_actual) > cash_tolerance:
            rep.breaks.append(Break("cash", "CASH", cash_expected, cash_actual))
    return rep


def require_clean(rep: Reconciliation) -> None:
    """The gate itself: raise rather than trade on an unverified book."""
    if not rep.clean:
        raise RuntimeError("تطبیق دفتر و کارگزار انجام نشده: " + rep.summary())
