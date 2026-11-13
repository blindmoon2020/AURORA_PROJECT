"""Transaction cost analysis: what execution actually cost, not what we assumed.

A backtest assumes a spread. Live fills reveal the truth: the gap between the
ticket price and the fill, the share of tickets that never filled, and how much
of the slippage happened on the side we did not plan for.
"""
from dataclasses import dataclass
from typing import Dict, List, Sequence

from ..stats import mean


@dataclass
class Fill:
    symbol: str
    side: str          # "BUY" or "SELL"
    units: float
    ticket_price: float
    fill_price: float


def slippage_bps(fill: Fill) -> float:
    """Positive means we paid worse than planned, on either side."""
    if fill.ticket_price <= 0:
        raise ValueError("ticket price must be positive")
    sign = 1.0 if fill.side.upper() == "BUY" else -1.0
    return (fill.fill_price - fill.ticket_price) / fill.ticket_price * 10_000 * sign


@dataclass
class TCAReport:
    fills: int
    notional_usd: float
    mean_slippage_bps: float
    worst_slippage_bps: float
    by_symbol: Dict[str, float]
    verdict: str


def analyse(fills: Sequence[Fill]) -> TCAReport:
    if not fills:
        return TCAReport(0, 0.0, 0.0, 0.0, {}, "no fills to analyse")
    slips = [slippage_bps(f) for f in fills]
    notional = sum(f.units * f.fill_price for f in fills)
    by_sym: Dict[str, List[float]] = {}
    for f, s in zip(fills, slips):
        by_sym.setdefault(f.symbol, []).append(s)
    avg = mean(slips)
    verdict = ("cost in line with the backtest assumption"
               if abs(avg) <= 3.0 else
               "execution worse than the model: recalibrate the cost table")
    return TCAReport(len(fills), notional, avg, min(slips),
                     {k: mean(v) for k, v in by_sym.items()}, verdict)
