"""Cross-asset allocation sleeve: the rules, as code the core can call.

This is path 2 promoted from a research script to a module, because a strategy that
only exists inside a script cannot be monitored, cannot be risk-limited and cannot be
refused when the audit says it should not run. The rules are frozen here as data, not
buried in a loop:

  12-month momentum with the most recent month skipped (the skip matters: the last
  month tends to reverse), long/cash only, inverse-volatility sizing, monthly cadence,
  no leverage, cost charged per unit of turnover.

Why this sleeve exists at all: an asset class does not delist, so unlike stock
selection on a survivor universe its test is not structurally biased. That is the
reason to run it, and it is the only claim made for it - the measured result was risk
control, not excess return.
"""
from dataclasses import dataclass
from statistics import pstdev
from typing import Dict, List, Optional, Sequence

from aurora.core.types import Candle

DAY = 86400


@dataclass(frozen=True)
class CrossAssetRules:
    lookback_days: int = 252
    skip_days: int = 21
    vol_window_days: int = 60
    cadence_days: int = 21
    cost_per_turnover: float = 0.0004
    max_weight_per_asset: float = 0.35
    min_vol: float = 1e-6
    min_history: int = 200

    def validate(self) -> None:
        if self.lookback_days <= self.skip_days:
            raise ValueError("lookback must exceed the skipped month")
        if self.min_weight_guard() > self.max_weight_per_asset:
            raise ValueError("a single-asset cap below the minimum weight is unusable")

    def min_weight_guard(self) -> float:
        return 1.0 / 20.0      # with 20+ assets inverse-vol never needs more


def momentum(closes: Sequence[float], lookback: int = 252, skip: int = 21) -> Optional[float]:
    """Return over the lookback, ending `skip` observations before today."""
    if len(closes) <= lookback or lookback <= skip:
        return None
    end = closes[-1 - skip]
    start = closes[-1 - lookback]
    if start <= 0:
        return None
    return end / start - 1.0


def realized_vol(closes: Sequence[float], window: int = 60,
                 periods_per_year: int = 252) -> Optional[float]:
    """Annualised volatility from the last `window` closes. None if too short."""
    if len(closes) <= window + 1:
        return None
    tail = closes[-window - 1:]
    rets = [tail[i] / tail[i - 1] - 1.0 for i in range(1, len(tail)) if tail[i - 1] > 0]
    if len(rets) < 20:
        return None
    return pstdev(rets) * (periods_per_year ** 0.5)


def sized_weights(features: Dict[str, dict], rules: CrossAssetRules = CrossAssetRules()) -> Dict[str, float]:
    """Inverse-volatility weights over assets whose momentum is positive.

    A positive momentum with no measurable volatility is skipped rather than sized at
    an arbitrary maximum: an instrument whose risk cannot be estimated cannot be
    risk-sized, and pretending otherwise is how a sleeve becomes a position.
    """
    active = {s: f for s, f in features.items()
              if f.get("momentum", 0.0) > 0 and (f.get("vol") or 0.0) > rules.min_vol}
    if not active:
        return {}
    raw = {s: 1.0 / f["vol"] for s, f in active.items()}
    return _apply_cap(raw, rules.max_weight_per_asset)


def _apply_cap(raw: Dict[str, float], cap: float) -> Dict[str, float]:
    """Cap and redistribute among the uncapped, so the cap actually holds.

    A single pass that caps and then renormalises pushes the capped asset back over
    its own limit - the opposite of the intent - so the redistribution is iterative.
    """
    capped: Dict[str, float] = {}
    free = dict(raw)
    while free:
        total = sum(free.values())
        if total <= 0:
            return {}
        weights = {s: v / total for s, v in free.items()}
        over = [s for s, w in weights.items() if w > cap + 1e-12]
        if not over:
            capped.update(weights)
            return capped
        for s in over:
            capped[s] = cap
            free.pop(s)
    # when every remaining asset is at its cap the rest stays in CASH. Renormalising
    # to 1.0 would breach the cap, and leverage is not a thing this sleeve does.
    return capped


def turnover(held: Dict[str, float], target: Dict[str, float]) -> float:
    return 0.5 * sum(abs(target.get(s, 0.0) - held.get(s, 0.0))
                     for s in set(held) | set(target))


def step(held: Dict[str, float], features: Dict[str, dict],
         rules: CrossAssetRules = CrossAssetRules()) -> tuple:
    """One rebalance: (new holdings, cost charged this period)."""
    target = sized_weights(features, rules)
    return target, turnover(held, target) * rules.cost_per_turnover


def sleeve_series(assets: Dict[str, Sequence[Candle]],
                  rules: CrossAssetRules = CrossAssetRules(),
                  calendar_symbol: str = "SPY") -> List[float]:
    """Per-rebalance returns of the sleeve. The calendar is ONE market's sessions."""
    ref = assets.get(calendar_symbol) or next(iter(assets.values()), [])
    if not ref:
        return []
    grid = [c.ts for c in ref]
    close = {s: {c.ts: c.close for c in cs} for s, cs in assets.items()}
    idx = {s: [c.close for c in cs] for s, cs in assets.items()}
    held: Dict[str, float] = {}
    out: List[float] = []
    for i in range(rules.min_history, len(grid) - rules.cadence_days, rules.cadence_days):
        ts, nxt = grid[i], grid[min(i + rules.cadence_days, len(grid) - 1)]
        features = {}
        for s, series in idx.items():
            pos = next((k for k, c in enumerate(assets[s]) if c.ts == ts), None)
            if pos is None or pos < rules.min_history:
                continue
            hist = series[:pos + 1]
            mom = momentum(hist, rules.lookback_days, rules.skip_days)
            vol = realized_vol(hist, rules.vol_window_days)
            if mom is not None and vol is not None:
                features[s] = {"momentum": mom, "vol": vol}
        target, cost = step(held, features, rules)
        fwd = 0.0
        for s, w in target.items():
            px0, px1 = close[s].get(ts), close[s].get(nxt)
            if px0 and px1:
                fwd += w * (px1 / px0 - 1.0)
        out.append(fwd - cost)
        held = target
    return out
