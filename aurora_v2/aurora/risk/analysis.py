"""Capacity and factor exposure: two questions a strategy must answer before money.

Capacity: how much could this book actually trade without moving the market?
Exposure: what is it really a bet on? A 20-name book that is 90% market beta is an
expensive index tracker, and the number says so before anyone funds it.
"""
import math
from dataclasses import dataclass
from typing import Dict, Sequence

from ..stats import mean, stdev


@dataclass
class Capacity:
    adtv_usd: float
    participation_cap: float          # fraction of daily volume we allow ourselves
    max_position_usd: float
    reason: str


def capacity(avg_price: float, avg_volume: float, participation: float = 0.01,
             book_usd: float = 1_000_000.0) -> Capacity:
    """ADTV-based capacity at a stated participation rate.

    Ten basis points of a day's volume is the usual ceiling for a strategy that
    needs to exit in a hurry; anything above that is a promise that the market
    will be there for us, which it will not be on the day we need it most.
    """
    if avg_price <= 0 or avg_volume < 0:
        raise ValueError("price must be positive and volume non-negative")
    if not 0 < participation <= 1:
        raise ValueError("participation must be in (0, 1]")
    adtv = avg_price * avg_volume
    cap = adtv * participation
    return Capacity(
        adtv_usd=adtv,
        participation_cap=participation,
        max_position_usd=cap,
        reason=(f"ADTV {adtv:,.0f} USD x {participation:.2%} = {cap:,.0f} USD per name; "
                f"a {book_usd:,.0f} USD book across 10 names needs {book_usd / 10:,.0f} "
                f"per name, {'within' if book_usd / 10 <= cap else 'ABOVE'} capacity"),
    )


@dataclass
class Exposure:
    market: float
    momentum: float
    residual_vol: float
    r_squared: float


def _window(xs: Sequence[float], i: int, n: int) -> Sequence[float]:
    return xs[max(0, i - n + 1):i + 1]


def factor_exposure(returns: Sequence[float], market: Sequence[float],
                    momentum_factor: Sequence[float] | None = None,
                    window: int = 252) -> Exposure:
    """Two-factor least squares on the trailing window. No intercept games."""
    n = min(len(returns), len(market), window)
    if n < 30:
        raise ValueError("need at least 30 overlapping observations")
    y = list(returns[-n:])
    x1 = list(market[-n:])
    x2 = list(momentum_factor[-n:]) if momentum_factor is not None else [0.0] * n

    # normal equations for y = b1*x1 + b2*x2 + e
    s11 = sum(v * v for v in x1)
    s22 = sum(v * v for v in x2)
    s12 = sum(a * b for a, b in zip(x1, x2))
    s1y = sum(a * b for a, b in zip(x1, y))
    s2y = sum(a * b for a, b in zip(x2, y))
    det = s11 * s22 - s12 * s12
    if abs(det) < 1e-18:
        b1 = s1y / s11 if s11 else 0.0
        b2 = 0.0
    else:
        b1 = (s22 * s1y - s12 * s2y) / det
        b2 = (s11 * s2y - s12 * s1y) / det

    resid = [yv - b1 * a - b2 * b for yv, a, b in zip(y, x1, x2)]
    var_y = stdev(y) ** 2
    r2 = 1.0 - (stdev(resid) ** 2) / var_y if var_y > 0 else 0.0
    return Exposure(market=b1, momentum=b2, residual_vol=stdev(resid) * math.sqrt(252),
                     r_squared=max(0.0, min(1.0, r2)))
