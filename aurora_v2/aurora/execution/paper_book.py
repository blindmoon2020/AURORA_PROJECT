"""Paper book: the only performance number money cannot buy is elapsed time.

A paper session is not a simulation of the backtest. It records the decision made
today with the data available today, then pays whatever the market asks on the
next open, and keeps the difference between the two. That difference is slippage,
and after enough sessions it becomes a measured number instead of an assumption.
"""
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from aurora.core.types import Candle


@dataclass
class Position:
    symbol: str
    weight: float
    decided_ts: int
    decided_price: float
    fill_price: Optional[float] = None
    fill_ts: Optional[int] = None


@dataclass
class PaperBook:
    started: str
    cash: float = 1.0
    equity: float = 1.0
    positions: List[Position] = field(default_factory=list)
    slippage_bps: List[float] = field(default_factory=list)
    sessions: int = 0

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, blob: dict) -> "PaperBook":
        book = cls(started=blob.get("started", ""), cash=blob.get("cash", 1.0),
                   equity=blob.get("equity", 1.0),
                   slippage_bps=list(blob.get("slippage_bps", [])),
                   sessions=int(blob.get("sessions", 0)))
        book.positions = [Position(**p) for p in blob.get("positions", [])]
        return book


def load(path: str | Path) -> Optional[PaperBook]:
    file = Path(path)
    if not file.exists():
        return None
    return PaperBook.from_json(json.loads(file.read_text(encoding="utf-8")))


def save(book: PaperBook, path: str | Path) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(book.to_json(), indent=2, ensure_ascii=False),
                    encoding="utf-8")


def apply_fills(book: PaperBook, candles: Dict[str, Sequence[Candle]]) -> List[dict]:
    """Resolve every unfilled position at the first open after the decision.

    A decision made on a close cannot be filled on that close. The fill is the next
    bar's open, and the gap between decision price and fill price is logged in basis
    points, signed so that paying more than expected is negative.
    """
    filled = []
    for pos in book.positions:
        if pos.fill_price is not None:
            continue
        series = candles.get(pos.symbol) or []
        nxt = next((c for c in series if c.ts > pos.decided_ts), None)
        if nxt is None:
            continue                      # market has not opened yet: stay pending
        pos.fill_price = float(nxt.open)
        pos.fill_ts = int(nxt.ts)
        if pos.decided_price > 0:
            bps = (pos.fill_price / pos.decided_price - 1.0) * 10000.0
            book.slippage_bps.append(bps)
            filled.append({"symbol": pos.symbol, "bps": bps})
    book.sessions += 1
    return filled


def rebalance(book: PaperBook, targets: Dict[str, float],
              closes: Dict[str, tuple[int, float]]) -> List[str]:
    """Replace the book with the new target weights, returning what changed."""
    wanted = {s: w for s, w in targets.items() if w > 0}
    changed = []
    for pos in list(book.positions):
        if pos.symbol not in wanted:
            changed.append(f"exit {pos.symbol}")
            book.positions.remove(pos)
    held = {p.symbol: p for p in book.positions}
    for sym, weight in wanted.items():
        ts, price = closes.get(sym, (0, 0.0))
        if sym in held:
            held[sym].weight = weight
            continue
        book.positions.append(Position(symbol=sym, weight=weight, decided_ts=int(ts),
                                       decided_price=float(price)))
        changed.append(f"enter {sym}")
    return changed


def mark_to_market(book: PaperBook, closes: Dict[str, tuple[int, float]]) -> float:
    """Equity relative to entry, weighted. A pending fill marks at its decision price."""
    total = 0.0
    for pos in book.positions:
        base = pos.fill_price or pos.decided_price
        _, price = closes.get(pos.symbol, (0, base))
        if base > 0:
            total += pos.weight * (price / base - 1.0)
    book.equity = 1.0 + total
    return book.equity
