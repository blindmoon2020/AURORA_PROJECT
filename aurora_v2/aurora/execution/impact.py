"""Pre-trade cost: market impact and execution latency, priced before the order goes.

Gemini's comparison was right that friction was modelled at a basic level: the code
had spread, commission, tax and measured slippage, but nothing that asks "how much
will THIS order move the price". Aladdin-class platforms simulate the order book
before sending; this module is the honest small version of that.

The model is the square-root law, the one that survives out-of-sample across markets:

    impact_bps = k * daily_vol_bps * sqrt(participation)      participation = size / ADV

k defaults to 10, the value used across equity and futures literature. It is labelled
an assumption, not a measurement, and the caller is told so.

Two refusals are built in, because a cost model that never says no is a decoration:
  - an order above the participation cap is REFUSED, not merely penalised
  - unknown ADV means unknown liquidity, which means no order, not a default order

Latency is modelled too. Manual execution (manual_bridge) adds human delay, and in a
fast market that delay is a real cost with a name and a number.
"""
from dataclasses import dataclass
from statistics import median
from typing import Optional, Sequence

DEFAULT_K = 10.0
DEFAULT_PARTICIPATION_CAP = 0.10


@dataclass(frozen=True)
class ImpactEstimate:
    notional: float
    participation: float          # order as a share of average daily volume
    impact_bps: float
    half_spread_bps: float
    total_bps: float
    allowed: bool
    reason: str = ""

    def cost_money(self) -> float:
        return self.notional * self.total_bps / 10000.0


def participation(notional: float, adv_notional: Optional[float]) -> Optional[float]:
    """Share of a day's traded value. None when liquidity is unknown."""
    if adv_notional is None or adv_notional <= 0:
        return None
    return abs(notional) / adv_notional


def estimate(notional: float, adv_notional: Optional[float], daily_vol_bps: float,
             half_spread_bps: float = 0.5, k: float = DEFAULT_K,
             cap: float = DEFAULT_PARTICIPATION_CAP) -> ImpactEstimate:
    """Pre-trade cost and permission for one order."""
    part = participation(notional, adv_notional)
    if part is None:
        return ImpactEstimate(notional, float("nan"), float("nan"), half_spread_bps,
                              float("nan"), False,
                              "refused: average daily volume unknown, so liquidity is unknown")
    if part > cap:
        impact = k * max(0.0, daily_vol_bps) * (part ** 0.5)
        return ImpactEstimate(notional, part, impact, half_spread_bps,
                              impact + half_spread_bps, False,
                              f"refused: {part:.1%} of daily volume exceeds the {cap:.0%} cap")
    impact = k * max(0.0, daily_vol_bps) * (part ** 0.5)
    return ImpactEstimate(notional, part, impact, half_spread_bps,
                          impact + half_spread_bps, True)


def split_order(notional: float, adv_notional: Optional[float],
                daily_vol_bps: float, half_spread_bps: float = 0.5,
                k: float = DEFAULT_K,
                cap: float = DEFAULT_PARTICIPATION_CAP) -> dict:
    """Slice a large order into cap-sized child orders and price the total.

    Slicing does not remove cost, it spreads it: each child pays its own impact and the
    sum is reported, so a plan that needs ten days is visible as ten days, not hidden.
    """
    part = participation(notional, adv_notional)
    if part is None:
        return {"slices": 0, "total_bps": float("nan"), "days": float("inf"),
                "allowed": False, "reason": "refused: liquidity unknown"}
    if part <= cap:
        est = estimate(notional, adv_notional, daily_vol_bps, half_spread_bps, k, cap)
        return {"slices": 1, "total_bps": est.total_bps, "days": 1.0,
                "allowed": est.allowed, "reason": est.reason}
    slices = int(-(-part // cap))            # ceiling division, stdlib only
    child = abs(notional) / slices
    costs = [estimate(child, adv_notional, daily_vol_bps, half_spread_bps, k, cap)
             for _ in range(slices)]
    total = sum(c.total_bps for c in costs) / len(costs)
    return {"slices": slices, "total_bps": total, "days": float(slices),
            "allowed": all(c.allowed for c in costs), "reason": "sliced to respect the cap"}


@dataclass(frozen=True)
class Latency:
    decision_to_order_s: float
    order_to_fill_s: float
    mode: str                    # "auto" or "manual"


MANUAL_SLA_S = 15 * 60          # a human ticket older than 15 minutes is a stale price
AUTO_SLA_S = 5.0


def latency_report(samples: Sequence[Latency]) -> dict:
    """Execution delay, and how much of it breaches the service level."""
    if not samples:
        return {"samples": 0, "median_s": 0.0, "p90_s": 0.0, "breaches": 0,
                "breach_rate": 0.0}
    delays = sorted(s.decision_to_order_s + s.order_to_fill_s for s in samples)
    bad = [s for s in samples
           if (s.decision_to_order_s + s.order_to_fill_s)
           > (MANUAL_SLA_S if s.mode == "manual" else AUTO_SLA_S)]
    return {"samples": len(samples), "median_s": median(delays),
            "p90_s": delays[int(0.9 * (len(delays) - 1))],
            "breaches": len(bad), "breach_rate": len(bad) / len(samples)}


def slippage_vs_impact(measured_bps: float, estimated: ImpactEstimate) -> str:
    """Did reality match the model? A model never checked is a guess with a formula."""
    if estimated.total_bps != estimated.total_bps:      # NaN
        return "unchecked: no estimate was possible"
    diff = measured_bps - estimated.total_bps
    if abs(diff) <= 0.25 * max(1.0, estimated.total_bps):
        return "model held"
    return (f"model underestimated by {diff:.1f} bps"
            if diff > 0 else f"model overestimated by {-diff:.1f} bps")
