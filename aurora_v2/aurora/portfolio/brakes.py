"""Three independent brakes, and the rule that decides which one is binding.

Institutions do not choose one allocation method. They stack several, each with a
different failure mode, and let the tightest one govern. That is the structure adopted
here, and it is deliberately conservative: three brakes that each answer a different
question, and no fourth that would only repeat one of them.

  1. VOL TARGET - is today's portfolio riskier than the risk budget says? (Bridgewater,
     AQR, Man AHL style.) Reacts continuously, and is the first to act.
  2. CRISIS CAP - if a named crisis repeated tomorrow, would the book breach its limit?
     (Aladdin-style scenario analysis.) Reacts to history we have not lived.
  3. DRAWDOWN BRAKE - we are already losing; how much more may we lose before we cut?
     (CPPIB/Man drawdown control.) Reacts to our own realised pain.

The overlay takes the MINIMUM, never the average: averaging brakes means the loosest one
weakens the others, which is how a risk framework becomes decorative. It also never
scales above 1: a brake that can lever up is not a brake.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aurora.portfolio.scenarios import crisis_exposure_cap


@dataclass
class OverlayDecision:
    scale: float
    binding: str
    parts: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        detail = "، ".join(f"{k}={v:.2f}" for k, v in self.parts.items())
        return f"مقیاس {self.scale:.2f} (محدودکننده: {self.binding}) — {detail}"


def vol_target_scale(current_vol: float, target_vol: float,
                     floor: float = 0.30) -> float:
    """Scale exposure so realised risk matches the budget. Never above 1 (no leverage)."""
    if target_vol <= 0 or current_vol <= 0:
        return 0.0
    return max(floor, min(1.0, target_vol / current_vol))


def drawdown_scale(drawdown_pct: float, soft: float = 10.0, hard: float = 20.0,
                   floor: float = 0.25) -> float:
    """Linear de-risking between a soft and a hard drawdown, floored, never leveraged.

    `drawdown_pct` is the current loss from peak as a positive number. Below the soft
    trigger nothing happens; at the hard level the book is cut to `floor`. Linear rather
    than a cliff, because a cliff creates an incentive to game the measurement.
    """
    dd = abs(drawdown_pct)
    if dd <= soft:
        return 1.0
    if dd >= hard:
        return floor
    span = hard - soft
    return max(floor, 1.0 - (dd - soft) / span * (1.0 - floor))


def smoothed_scale(new_scale: float, previous_scale: Optional[float] = None,
                   min_increase: float = 0.05) -> float:
    """De-risk at once, re-risk slowly. The asymmetry is the point.

    Recomputing the scale every session would trade a little on every wobble in the stress
    replay, and each of those trades pays commission to move money a few percent. So a cut
    is taken immediately (a brake that waits is not a brake), while a rise is only taken
    when it is materially larger than the last scale. That is what makes the overlay cheap
    as well as safe.
    """
    if previous_scale is None:
        return new_scale
    if new_scale < previous_scale:
        return new_scale
    if new_scale - previous_scale > min_increase:
        return new_scale
    return previous_scale


def decide(weights: Dict[str, float], current_vol: Optional[float] = None,
           target_vol: Optional[float] = None, drawdown_pct: float = 0.0,
           limit_pct: float = 40.0, reserved_exposure: float = 0.0,
           previous_scale: Optional[float] = None,
           min_increase: float = 0.05) -> OverlayDecision:
    """Combine the brakes. The tightest governs; every part is reported, not just the winner."""
    parts: Dict[str, float] = {}
    notes: List[str] = []

    # the sleeve's budget is reserved exposure: it is not in `weights` yet, but a crisis
    # does not wait for the second sleeve to be built. Treating it as equity in the replay
    # is conservative, and being conservative here is the whole point of the brake.
    stress_weights = dict(weights)
    if reserved_exposure:
        stress_weights["__reserved_sleeve__"] = reserved_exposure

    if stress_weights:
        cap = crisis_exposure_cap(stress_weights, limit_pct)
        parts["crisis"] = max(0.0, min(1.0, cap["scale"]))
        if cap["scale"] < 1.0:
            notes.append(f"سقف بحران: بدترین سناریو {cap['binding_scenario']} با "
                         f"{cap['worst_loss_pct']:.1f}% حد {limit_pct:.0f}% را می‌شکست")

    if current_vol and target_vol:
        parts["vol"] = vol_target_scale(current_vol, target_vol)
        if parts["vol"] < 1.0:
            notes.append(f"هدف نوسان: نوسان فعلی {current_vol:.0%} از هدف {target_vol:.0%} بیشتر است")

    if drawdown_pct:
        parts["drawdown"] = drawdown_scale(drawdown_pct)
        if parts["drawdown"] < 1.0:
            notes.append(f"ترمز افت: افت فعلی {abs(drawdown_pct):.1f}% از آستانه گذشته است")

    if not parts:
        return OverlayDecision(1.0, "هیچ", {}, ["داده کافی برای هیچ ترمزی نبود: مقیاس کامل"])

    binding = min(parts, key=lambda k: parts[k])
    raw = min(1.0, parts[binding])
    scale = smoothed_scale(raw, previous_scale, min_increase)
    if previous_scale is not None and scale != raw:
        notes.append(f"مقیاس روی {scale:.2f} نگه داشته شد (اختلاف {raw:.2f} کمتر از "
                     f"آستانه {min_increase:.0%} است): افزایش مواجهه فقط در گام معنادار")
    return OverlayDecision(scale, binding, parts, notes)


def apply_overlay(weights: Dict[str, float], decision: OverlayDecision) -> Dict[str, float]:
    """Scale every target by the overlay. Cash is what is left, never a negative position."""
    return {sym: round(w * decision.scale, 6) for sym, w in weights.items()}
