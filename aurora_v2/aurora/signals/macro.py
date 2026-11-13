"""Macro regime: the backdrop that decides how much conviction a ranking deserves.

A cross-sectional ranking says "X is the best of these names". It cannot say
"today is a bad day to own anything". This module answers the second question
with four inputs any allocator can defend, and fixed thresholds written down here
so they cannot be tuned after seeing the result.

Institutional practice in 2026 leans on exactly this shape: regime awareness
before stock selection, because factor payoffs shift with the macro backdrop.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .factors import RankedAsset


@dataclass(frozen=True)
class Regime:
    score: float          # -1 hostile, 0 neutral, +1 supportive
    label: str
    inputs: Dict[str, Optional[float]]


THRESHOLDS = {
    "vix": (15.0, 25.0),          # below, between, above
    "curve_bp": (0.0, 50.0),
    "credit_bp": (350.0, 600.0),
    "real_rate": (0.0, 2.0),
}


def _band(value: Optional[float], low: float, high: float, invert: bool = False) -> Optional[float]:
    """+1 when comfortable, 0 in the middle, -1 when stressed."""
    if value is None:
        return None
    if invert:
        return 1.0 if value > high else (0.0 if value > low else -1.0)
    return 1.0 if value < low else (0.0 if value < high else -1.0)


def regime(
    vix: Optional[float],
    curve_bp: Optional[float],
    credit_bp: Optional[float],
    real_rate: Optional[float],
) -> Regime:
    parts = {
        "vix": _band(vix, *THRESHOLDS["vix"]),
        "curve_bp": _band(curve_bp, *THRESHOLDS["curve_bp"], invert=True),
        "credit_bp": _band(credit_bp, *THRESHOLDS["credit_bp"]),
        "real_rate": _band(real_rate, *THRESHOLDS["real_rate"]),
    }
    known = [v for v in parts.values() if v is not None]
    if not known:
        return Regime(0.0, "unknown", parts)
    score = sum(known) / len(known)
    label = "supportive" if score > 0.25 else ("hostile" if score < -0.25 else "neutral")
    return Regime(score=score, label=label, inputs=parts)


def tilt(ranked: List[RankedAsset], reg: Regime, strength: float = 0.5) -> List[RankedAsset]:
    """Dampen or lift every score by the backdrop, without changing the order.

    Only the magnitude changes: a hostile backdrop shrinks conviction, it does not
    re-rank the names, because the ranking has no information about the regime.
    """
    factor = 1.0 + strength * reg.score
    return [RankedAsset(symbol=r.symbol, score=r.score * factor,
                        components=r.components, reason=r.reason) for r in ranked]


def point_in_time(rows: List[dict], as_of_ts: int, date_field: str = "filing_date") -> Optional[dict]:
    """The most recent filing that was actually public at `as_of_ts`.

    This is the whole defence against look-ahead bias: a 2026 annual report does
    not exist in 2019, however convenient it would be for the backtest.
    """
    from datetime import datetime, timezone

    best, best_ts = None, -1
    for row in rows:
        raw = row.get(date_field)
        if not raw:
            continue
        try:
            ts = int(datetime.strptime(str(raw)[:10], "%Y-%m-%d")
                     .replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            continue
        if ts <= as_of_ts and ts > best_ts:
            best, best_ts = row, ts
    return best
