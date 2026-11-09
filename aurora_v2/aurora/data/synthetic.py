"""Deterministic synthetic candles, so every module can be tested with no data feed.

A random walk is not a market. It is a fixture: it proves the plumbing runs and
that sizing, stops and accounting behave. It says nothing about edge.
"""
from __future__ import annotations

import random
from typing import List

from ..core.types import Candle


def synthetic_candles(
    n: int = 5000,
    seed: int = 7,
    start: float = 1.0850,
    bar_seconds: int = 3600,
    vol: float = 0.00045,
    wick: float = 0.00025,
    trend: float = 0.0,
) -> List[Candle]:
    rng = random.Random(seed)
    price, out = start, []
    for i in range(n):
        o = price
        price = max(0.01, price + rng.gauss(trend, vol))
        hi = max(o, price) + abs(rng.gauss(0, wick))
        lo = min(o, price) - abs(rng.gauss(0, wick))
        out.append(Candle(ts=i * bar_seconds, open=o, high=hi, low=lo, close=price))
    return out
