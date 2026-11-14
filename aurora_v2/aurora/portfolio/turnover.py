"""Turnover control: the difference between a model and a fee generator.

At a 124 bps round trip (Tehran bourse) a monthly rebalance that chases small
ranking changes pays roughly 15% a year for movements that are mostly noise. The
fix is not a better model, it is a band: a position is only touched when it has
drifted far enough that the expected gain exceeds the cost of the trade.

Two bands, because they answer different questions:
  absolute  - a 10% target that has drifted to 11.5% is 1.5 points, however you look
  relative  - the same drift matters more on a small allocation than a large one

Exits are never band-limited: a target of zero means the reason for holding is gone,
and waiting for drift would keep a position nobody wants any more.
"""
from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


@dataclass(frozen=True)
class Band:
    abs_band: float = 0.02         # weight drift that justifies a trade
    rel_band: float = 0.25         # or this fraction of the target weight
    min_trade_weight: float = 0.01 # never trade dust, whatever the band says

    def allows(self, current: float, target: float) -> bool:
        drift = abs(target - current)
        if drift < self.min_trade_weight:
            return False
        if drift <= self.abs_band:
            return False
        if target > 0 and drift <= self.rel_band * target:
            return False
        return True


def apply_band(current: Dict[str, float], target: Dict[str, float],
               band: Band = Band()) -> Tuple[Dict[str, float], Dict[str, str]]:
    """Adjusted targets, plus the reason for every position that was left alone.

    Exits always execute. Entries and size changes must clear the band.
    """
    adjusted: Dict[str, float] = {}
    skipped: Dict[str, str] = {}

    for sym in sorted(set(current) | set(target)):
        cur = current.get(sym, 0.0)
        tgt = target.get(sym, 0.0)
        if tgt <= 0:
            if cur > 0:
                adjusted[sym] = 0.0          # exit: never held for band reasons
            continue
        if cur <= 0:
            adjusted[sym] = tgt              # new position
            continue
        if band.allows(cur, tgt):
            adjusted[sym] = tgt
        else:
            adjusted[sym] = cur
            skipped[sym] = (f"drift {abs(tgt - cur):.3f} inside band "
                            f"(abs {band.abs_band:.3f} / rel {band.rel_band:.0%})")
    return adjusted, skipped


def turnover(current: Dict[str, float], new: Dict[str, float]) -> float:
    """One-way turnover: half the sum of absolute weight changes."""
    return 0.5 * sum(abs(new.get(s, 0.0) - current.get(s, 0.0))
                     for s in set(current) | set(new))


def trade_cost(turnover_one_way: float, cost_rate: float) -> float:
    """Cost as a fraction of the book for a given one-way turnover."""
    return turnover_one_way * cost_rate


def break_even_edge(turnover_one_way: float, cost_rate: float, periods_per_year: int = 12) -> float:
    """Annual return the model must add just to pay for trading this often."""
    return trade_cost(turnover_one_way, cost_rate) * periods_per_year


def sweep(current: Dict[str, float], target: Dict[str, float],
          cost_rate: float, bands: Iterable[float] = (0.0, 0.01, 0.02, 0.03, 0.05)) -> list:
    """Cost of each band, so the choice is made on numbers rather than taste."""
    rows = []
    for b in bands:
        adj, skipped = apply_band(current, target, Band(abs_band=b, rel_band=1.0))
        t = turnover(current, adj)
        rows.append({"band": b, "turnover": t,
                     "cost": trade_cost(t, cost_rate),
                     "annual_cost": break_even_edge(t, cost_rate),
                     "positions_skipped": len(skipped)})
    return rows
