"""Carry, defended. Three separate protections, each measurable on its own.

1. inverse-volatility weights   - the lira must not outvote the franc
2. a risk-off gate              - when the market is stressed, carry loses money
                                  exactly when it is most crowded, so stand down
3. an exclusion list            - pegged or managed currencies are not carry
                                  trades, they are option sales against a central
                                  bank; the payoff is a straight line until it isn't

Keeping them separate is the point: a single blended "improvement" cannot be
judged, and a defence that does not earn its keep must be droppable.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from ..stats import stdev


def regime_mask(
    ts_list: Sequence[int],
    vix: Dict[int, float],
    credit_spread: Optional[Dict[int, float]] = None,
    vix_cut: float = 25.0,
    spread_cut: float = 5.0,
) -> List[float]:
    """1.0 when risk is on, 0.0 when the market is stressed. Unknown means off.

    Standing down on missing data is deliberate: "we could not see the regime" is
    not evidence that the regime is calm.
    """
    from bisect import bisect_right

    vkeys = sorted(vix)
    skeys = sorted(credit_spread) if credit_spread else []

    def latest(keys, table, ts):
        i = bisect_right(keys, ts) - 1
        return table[keys[i]] if i >= 0 else None

    out: List[float] = []
    for ts in ts_list:
        v = latest(vkeys, vix, ts)
        if v is None:
            out.append(0.0)
            continue
        if v > vix_cut:
            out.append(0.0)
            continue
        if skeys:
            sp = latest(skeys, credit_spread or {}, ts)
            if sp is None or sp > spread_cut:
                out.append(0.0)
                continue
        out.append(1.0)
    return out


def inverse_vol_scale(
    returns: Sequence[float],
    window: int = 60,
    target: float = 0.10,
    cap: float = 3.0,
) -> List[float]:
    """Scale each day's position by target/realised-vol, capped."""
    out: List[float] = []
    for i in range(len(returns)):
        start = max(0, i - window + 1)
        chunk = returns[start:i + 1]
        vol = stdev(chunk) * (252 ** 0.5) if len(chunk) > 1 else 0.0
        out.append(min(cap, target / vol) if vol > 1e-9 else 0.0)
    return out


def apply_defences(
    positions: Sequence[float],
    scale: Optional[Sequence[float]] = None,
    mask: Optional[Sequence[float]] = None,
) -> List[float]:
    if scale is not None and len(scale) != len(positions):
        raise ValueError("scale must line up with positions")
    if mask is not None and len(mask) != len(positions):
        raise ValueError("mask must line up with positions")
    out = []
    for i, p in enumerate(positions):
        v = p
        if scale is not None:
            v *= scale[i]
        if mask is not None:
            v *= mask[i]
        out.append(v)
    return out
