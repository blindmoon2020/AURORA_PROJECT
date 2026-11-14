"""Targets in, broker-ready ticket lines out, fills back in.

Sizing rule: units are computed from the price at decision time and the equity of
the book, so the human copying the line does not do arithmetic. Every ticket
expires, because a limit price that is a day old is not a price any more.
"""
from typing import Dict, List, Optional, Sequence

from aurora.core.types import Side
from aurora.execution.manual import (FillRecord, ManualExecutionError, OrderTicket,
                                     reconcile, render, ticket)


def tickets_for_targets(targets: Dict[str, float], prices: Dict[str, float],
                        equity: float, decision_id: str, created_ts: int,
                        ttl_seconds: int = 6 * 3600,
                        limit_buffer_bps: float = 0.0) -> List[OrderTicket]:
    """One ticket per target with a price. A target without a price is skipped loudly."""
    out: List[OrderTicket] = []
    missing: List[str] = []
    for seq, (sym, weight) in enumerate(sorted(targets.items()), start=1):
        price = prices.get(sym)
        if not price or price <= 0:
            missing.append(sym)
            continue
        units = equity * weight / price
        if units <= 0:
            continue
        limit = price * (1 + limit_buffer_bps / 10_000) if limit_buffer_bps else None
        out.append(ticket(decision_id, sym, Side.LONG, units, created_ts,
                          ttl_seconds=ttl_seconds, limit_price=limit,
                          note=f"{weight:.1%} of book", seq=seq))
    if missing:
        raise ManualExecutionError(f"no price for {', '.join(sorted(missing))}: "
                                   "a ticket without a price is a guess")
    return out


def book_from_fills(fills: Sequence[FillRecord], equity: float) -> Dict[str, float]:
    """Turn the broker's fill export into weights the paper book can hold."""
    if not fills:
        return {}
    notionals: Dict[str, float] = {}
    for f in fills:
        sign = 1.0 if f.side == Side.LONG else -1.0
        notionals[f.symbol] = notionals.get(f.symbol, 0.0) + sign * f.units * f.price
    gross = sum(abs(v) for v in notionals.values())
    if gross <= 0:
        return {}
    # weights are relative to the book that was actually deployed, not the target
    return {s: v / gross for s, v in notionals.items() if abs(v) > 0}


def session_summary(tickets: Sequence[OrderTicket], fills: Sequence[FillRecord]) -> str:
    rec = reconcile(tickets, fills)
    expired = [t for t in rec.unfilled if t.expires_ts <= max((f.ts for f in fills), default=0)]
    lines = [rec.summary()]
    if expired:
        lines.append(f"{len(expired)} ticket(s) expired unfilled: "
                     + ", ".join(t.symbol for t in expired))
    if rec.unexpected:
        lines.append("unrecognised fills: " + ", ".join(f.symbol for f in rec.unexpected))
    return " | ".join(lines)
