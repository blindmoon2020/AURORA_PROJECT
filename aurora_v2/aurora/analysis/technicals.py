"""Technical structure, not indicator soup.

Everything here reads only closed candles. Nothing predicts; each function describes
where price is, where it has reacted, and how much volume changed hands. Any of these
can become a strategy feature, but a feature is not an edge: it still has to survive
the walk-forward gate with real costs.

Volume profile needs real volume. On FX spot there is none, so it returns a
volume-less profile flagged `has_volume=False` and must not be used as if it were one.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.types import Candle

FIB_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)
FIB_EXT = (1.272, 1.618)


@dataclass(frozen=True)
class Level:
    price: float
    touches: int
    kind: str          # "support" | "resistance"
    strength: float    # touches weighted by recency


@dataclass(frozen=True)
class Pattern:
    name: str
    index: int
    bias: int          # +1 bullish, -1 bearish, 0 neutral


def atr(candles: Sequence[Candle], period: int = 14) -> float:
    """Wilder ATR over the last `period` bars."""
    if len(candles) < 2:
        return 0.0
    trs: List[float] = []
    for prev, cur in zip(candles[:-1], candles[1:]):
        trs.append(max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close)))
    window = trs[-period:]
    if not window:
        return 0.0
    value = sum(window) / len(window)
    for tr in trs[len(trs) - period + 1:] if len(trs) > period else []:
        value = (value * (period - 1) + tr) / period
    return value


def swings(candles: Sequence[Candle], k: int = 3) -> List[Tuple[int, float, str]]:
    """Local extremes: bar whose high (low) is the max (min) of the 2k+1 window."""
    out: List[Tuple[int, float, str]] = []
    if len(candles) < 2 * k + 1:
        return out
    for i in range(k, len(candles) - k):
        window = candles[i - k:i + k + 1]
        if candles[i].high >= max(c.high for c in window):
            out.append((i, candles[i].high, "high"))
        if candles[i].low <= min(c.low for c in window):
            out.append((i, candles[i].low, "low"))
    return out


def support_resistance(candles: Sequence[Candle], k: int = 3, tolerance_atr: float = 0.35,
                       max_levels: int = 8) -> List[Level]:
    """Cluster swing prices into levels; strength decays with age and grows with touches."""
    atr_value = atr(candles)
    tol = tolerance_atr * atr_value if atr_value > 0 else 0.0
    if tol <= 0:
        return []
    last = candles[-1].close
    n = len(candles)
    clusters: List[Dict] = []
    for index, price, _kind in swings(candles, k):
        for c in clusters:
            if abs(c["price"] - price) <= tol:
                c["prices"].append(price)
                c["touches"] += 1
                c["recency"] += index / n
                break
        else:
            clusters.append({"price": price, "prices": [price], "touches": 1, "recency": index / n})
    levels = []
    for c in clusters:
        price = sum(c["prices"]) / len(c["prices"])
        levels.append(Level(price=price, touches=c["touches"],
                            kind="resistance" if price > last else "support",
                            strength=round(c["touches"] * (0.5 + c["recency"] / max(c["touches"], 1)), 4)))
    levels.sort(key=lambda lv: (lv.strength, lv.touches), reverse=True)
    return levels[:max_levels]


def fibonacci(candles: Sequence[Candle], lookback: int = 120) -> Dict[str, object]:
    """Retracement of the dominant swing leg inside `lookback`, plus extensions."""
    window = candles[-lookback:] if len(candles) > lookback else list(candles)
    if len(window) < 3:
        return {}
    hi_i = max(range(len(window)), key=lambda i: window[i].high)
    lo_i = min(range(len(window)), key=lambda i: window[i].low)
    high, low = window[hi_i].high, window[lo_i].low
    span = high - low
    if span <= 0:
        return {}
    direction = "up" if lo_i < hi_i else "down"
    levels = {}
    for r in FIB_RATIOS:
        levels[r] = high - span * r if direction == "up" else low + span * r
    extensions = {}
    for e in FIB_EXT:
        extensions[e] = low + span * e if direction == "up" else high - span * e
    return {"direction": direction, "high": high, "low": low, "span": span,
            "levels": levels, "extensions": extensions,
            "close": window[-1].close}


def volume_profile(candles: Sequence[Candle], bins: int = 24) -> Dict[str, object]:
    """Point of control and 70% value area. Requires real volume."""
    usable = [c for c in candles if c.volume and c.volume > 0]
    if not usable:
        return {"has_volume": False, "poc": None, "value_area": None, "profile": []}
    lo = min(c.low for c in usable)
    hi = max(c.high for c in usable)
    if hi <= lo:
        return {"has_volume": False, "poc": None, "value_area": None, "profile": []}
    width = (hi - lo) / bins
    buckets = [0.0] * bins
    for c in usable:
        typical = (c.high + c.low + c.close) / 3
        idx = min(bins - 1, max(0, int((typical - lo) / width)))
        buckets[idx] += c.volume
    total = sum(buckets)
    poc_i = max(range(bins), key=lambda i: buckets[i])
    lo_i = hi_i = poc_i
    covered = buckets[poc_i]
    while covered < 0.7 * total and (lo_i > 0 or hi_i < bins - 1):
        left = buckets[lo_i - 1] if lo_i > 0 else -1.0
        right = buckets[hi_i + 1] if hi_i < bins - 1 else -1.0
        if right >= left:
            hi_i += 1
            covered += buckets[hi_i]
        else:
            lo_i -= 1
            covered += buckets[lo_i]
    profile = [(lo + (i + 0.5) * width, round(buckets[i], 2)) for i in range(bins)]
    return {"has_volume": True,
            "poc": lo + (poc_i + 0.5) * width,
            "value_area": (lo + lo_i * width, lo + (hi_i + 1) * width),
            "profile": profile}


def price_action(candles: Sequence[Candle], bos_lookback: int = 20) -> List[Pattern]:
    """Last-bar structure only: engulfing, pin, doji, inside bar, break of structure."""
    out: List[Pattern] = []
    if len(candles) < 3:
        return out
    cur, prev = candles[-1], candles[-2]
    i = len(candles) - 1
    body, rng = cur.close - cur.open, cur.high - cur.low
    if rng > 0:
        upper = cur.high - max(cur.open, cur.close)
        lower = min(cur.open, cur.close) - cur.low
        if body > 0 and prev.close < prev.open and cur.close > prev.open and cur.open < prev.close:
            out.append(Pattern("bullish_engulfing", i, 1))
        if body < 0 and prev.close > prev.open and cur.close < prev.open and cur.open > prev.close:
            out.append(Pattern("bearish_engulfing", i, -1))
        if lower > 2 * abs(body) and upper < abs(body):
            out.append(Pattern("hammer", i, 1))
        if upper > 2 * abs(body) and lower < abs(body):
            out.append(Pattern("shooting_star", i, -1))
        if abs(body) < 0.1 * rng:
            out.append(Pattern("doji", i, 0))
    if cur.high <= prev.high and cur.low >= prev.low:
        out.append(Pattern("inside_bar", i, 0))
    if len(candles) > bos_lookback:
        prior = candles[-bos_lookback - 1:-1]
        if cur.close > max(c.high for c in prior):
            out.append(Pattern("bos_up", i, 1))
        elif cur.close < min(c.low for c in prior):
            out.append(Pattern("bos_down", i, -1))
    return out


def range_position(candles: Sequence[Candle], lookback: int = 50) -> Optional[float]:
    """0 = bottom of the recent range, 1 = top. None when there is no range."""
    window = candles[-lookback:] if len(candles) > lookback else list(candles)
    if not window:
        return None
    hi = max(c.high for c in window)
    lo = min(c.low for c in window)
    if hi <= lo:
        return None
    return (window[-1].close - lo) / (hi - lo)
