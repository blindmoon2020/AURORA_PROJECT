"""The decision surface: one ranked answer per asset, with the reasons attached.

AURORA is a platform that says what to buy and why, not a bot that fires orders.
Three rules keep it honest:

  * every factor is a cross-sectional z-score, so "cheap" means cheaper than the
    others being compared, never cheaper than an absolute threshold
  * a missing factor is dropped and its weight redistributed, never filled with
    zero, because zero is the median and pretending to know it is worse than
    admitting the input is absent
  * the reason string names the two factors that moved the score most, so a
    reader can disagree with the model instead of trusting it
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Dict, List, Optional, Sequence

from ..core.types import Candle


@dataclass(frozen=True)
class RankedAsset:
    symbol: str
    score: float
    components: Dict[str, float]
    reason: str


def zscore(values: Dict[str, float], clip: float = 3.0) -> Dict[str, float]:
    """Cross-sectional z-scores; fewer than three names means no ranking."""
    if len(values) < 3:
        return {}
    xs = list(values.values())
    mu, sd = mean(xs), stdev(xs)
    if sd <= 1e-12:
        return {}
    return {k: max(-clip, min(clip, (v - mu) / sd)) for k, v in values.items()}


def trend_of(candles: Sequence[Candle], lookback: int = 252, skip: int = 21) -> Optional[float]:
    if len(candles) < lookback + skip + 1:
        return None
    end, start = candles[-skip - 1].close, candles[-lookback - skip - 1].close
    return (end / start - 1.0) if start > 0 else None


def vol_of(candles: Sequence[Candle], window: int = 60) -> Optional[float]:
    if len(candles) < window + 2:
        return None
    closes = [c.close for c in candles[-(window + 1):]]
    rets = [closes[i] / closes[i - 1] - 1.0 for i in range(1, len(closes))]
    if len(rets) < 3:
        return None
    return stdev(rets) * (252 ** 0.5)


def build_factors(
    candles: Dict[str, Sequence[Candle]],
    fundamentals: Optional[Dict[str, Dict[str, float]]] = None,
    carry: Optional[Dict[str, float]] = None,
) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for symbol, series in candles.items():
        row: Dict[str, float] = {}
        t = trend_of(series)
        if t is not None:
            row["trend"] = t
        v = vol_of(series)
        if v is not None and v > 0:
            row["low_vol"] = -v
        f = (fundamentals or {}).get(symbol, {})
        if f.get("pe_ttm"):
            row["value"] = 1.0 / f["pe_ttm"]
        if f.get("roe") is not None:
            row["quality"] = f["roe"]
        if carry and symbol in carry:
            row["carry"] = carry[symbol]
        if row:
            out[symbol] = row
    return out


def composite(
    factors: Dict[str, Dict[str, float]],
    weights: Optional[Dict[str, float]] = None,
) -> List[RankedAsset]:
    weights = weights or {"trend": 0.40, "value": 0.25, "quality": 0.20, "low_vol": 0.15}
    names = sorted({f for row in factors.values() for f in row})
    zs = {name: zscore({s: row[name] for s, row in factors.items() if name in row})
          for name in names}

    ranked: List[RankedAsset] = []
    for symbol, row in factors.items():
        usable = {f: weights[f] for f in row
                  if f in weights and zs.get(f, {}).get(symbol) is not None}
        total_w = sum(usable.values())
        if total_w <= 0:
            continue
        components = {f: zs[f][symbol] for f in usable}
        score = sum(components[f] * (usable[f] / total_w) for f in components)
        top = sorted(components.items(), key=lambda kv: abs(kv[1]), reverse=True)[:2]
        reason = ", ".join(f"{f} {z:+.2f}" for f, z in top)
        ranked.append(RankedAsset(symbol=symbol, score=score, components=components, reason=reason))
    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked
