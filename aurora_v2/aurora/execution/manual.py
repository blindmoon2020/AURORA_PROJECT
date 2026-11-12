"""Manual execution: order tickets out, broker fills in, nothing invented in between.

Some venues have no API at all. The temptation is to scrape a broker portal or to
assume a fill at the signal price; both are lies that later look like performance.
This adapter keeps the core honest in three steps:

  1. `ticket()` turns a decision into a human-executable order with an expiry.
  2. the human places it in the broker and exports the day's fills.
  3. `reconcile()` matches what actually happened against what was asked, and names
     every ticket nobody filled and every fill nobody asked for.

A ticket is not a position. Until a fill arrives, the book is unchanged.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from ..core.types import Side

FILL_COLUMNS = ("ticket_id", "ts", "symbol", "side", "units", "price", "fee")


class ManualExecutionError(ValueError):
    """A ticket or fill file that cannot be trusted."""


@dataclass(frozen=True)
class OrderTicket:
    ticket_id: str
    decision_id: str
    symbol: str
    side: Side
    units: float
    limit_price: Optional[float]
    created_ts: int
    expires_ts: int
    note: str = ""

    def line(self) -> str:
        side = "BUY" if self.side == Side.LONG else "SELL"
        limit = f"{self.limit_price:.4f}" if self.limit_price else "market"
        return (f"{self.ticket_id} | {side:4s} {self.symbol:12s} {self.units:>12,.2f} "
                f"@ {limit} | expires {self.expires_ts} | {self.note}".rstrip())


@dataclass(frozen=True)
class FillRecord:
    ticket_id: str
    ts: int
    symbol: str
    side: Side
    units: float
    price: float
    fee: float = 0.0


@dataclass
class Reconciliation:
    matched: List[tuple] = field(default_factory=list)
    unfilled: List[OrderTicket] = field(default_factory=list)
    unexpected: List[FillRecord] = field(default_factory=list)
    price_slippage_bps: List[float] = field(default_factory=list)

    @property
    def filled_units(self) -> float:
        return sum(f.units for _, f in self.matched)

    def summary(self) -> str:
        slip = (f"{sum(self.price_slippage_bps) / len(self.price_slippage_bps):+.1f} bps"
                if self.price_slippage_bps else "n/a")
        return (f"{len(self.matched)} filled, {len(self.unfilled)} unfilled, "
                f"{len(self.unexpected)} unrecognised | mean slippage {slip}")


def ticket(decision_id: str, symbol: str, side: Side, units: float, created_ts: int,
           ttl_seconds: int = 3600, limit_price: Optional[float] = None,
           note: str = "", seq: int = 1) -> OrderTicket:
    """A ticket that expires, because a stale price is not a price."""
    if units <= 0:
        raise ManualExecutionError(f"units must be positive, got {units}")
    if ttl_seconds <= 0:
        raise ManualExecutionError("ttl_seconds must be positive")
    tid = f"{decision_id}-{seq:02d}"
    return OrderTicket(ticket_id=tid, decision_id=decision_id, symbol=symbol, side=side,
                       units=float(units), limit_price=limit_price, created_ts=created_ts,
                       expires_ts=created_ts + ttl_seconds, note=note)


def render(tickets: Sequence[OrderTicket]) -> str:
    head = "ticket      | side symbol              units        @ price    | expires"
    return "\n".join([head, "-" * len(head)] + [t.line() for t in tickets])


def parse_fills(text: str) -> List[FillRecord]:
    """Read the broker export. Unknown columns are ignored, wrong ones are refused."""
    text = text.lstrip("\ufeff").strip()
    if not text:
        return []
    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in FILL_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ManualExecutionError(f"fill file is missing columns: {', '.join(missing)}")
    fills: List[FillRecord] = []
    for i, row in enumerate(reader, start=2):
        try:
            side_raw = (row["side"] or "").strip().upper()
            if side_raw in ("BUY", "B", "LONG", "خرید"):
                side = Side.LONG
            elif side_raw in ("SELL", "S", "SHORT", "فروش"):
                side = Side.SHORT
            else:
                raise ManualExecutionError(f"row {i}: unknown side {row['side']!r}")
            units = float(row["units"])
            price = float(row["price"])
            if units <= 0 or price <= 0:
                raise ManualExecutionError(f"row {i}: units and price must be positive")
            fills.append(FillRecord(ticket_id=row["ticket_id"].strip(), ts=int(float(row["ts"])),
                                    symbol=row["symbol"].strip(), side=side, units=units,
                                    price=price, fee=float(row.get("fee") or 0.0)))
        except (TypeError, ValueError) as exc:
            if isinstance(exc, ManualExecutionError):
                raise
            raise ManualExecutionError(f"row {i}: {exc}") from exc
    return fills


def reconcile(tickets: Iterable[OrderTicket], fills: Iterable[FillRecord]) -> Reconciliation:
    by_id: Dict[str, OrderTicket] = {t.ticket_id: t for t in tickets}
    out = Reconciliation()
    seen = set()
    for f in fills:
        t = by_id.get(f.ticket_id)
        if t is None:
            out.unexpected.append(f)
            continue
        if f.ticket_id in seen:
            raise ManualExecutionError(f"ticket {f.ticket_id} filled twice")
        seen.add(f.ticket_id)
        if f.side != t.side:
            raise ManualExecutionError(
                f"ticket {t.ticket_id}: fill is {f.side} but the ticket was {t.side}")
        out.matched.append((t, f))
        ref = t.limit_price
        if ref:
            sign = 1.0 if t.side == Side.LONG else -1.0
            out.price_slippage_bps.append(sign * (f.price - ref) / ref * 10_000.0)
    out.unfilled = [t for t in by_id.values() if t.ticket_id not in seen]
    return out
